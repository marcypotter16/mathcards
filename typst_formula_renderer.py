from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class FormulaResult:
    name: str
    png_path: Path
    success: bool
    return_code: int
    stdout: str
    stderr: str


class TypstFormulaRenderer:
    def __init__(
        self,
        cache_directory: Path | str = "cache",
        padding_pt: float = 1.0,
    ) -> None:
        self.cache_directory = Path(cache_directory)
        self.padding_pt = padding_pt
        self.executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="typst",
        )
        self.pending: dict[str, Future[FormulaResult]] = {}

    def compile_formula(
        self,
        formula: str,
        name: str,
        ppi: int,
        frac_inline: bool = True
    ) -> FormulaResult:
        self.cache_directory.mkdir(parents=True, exist_ok=True)

        typ_path = self.cache_directory / f"{name}@{ppi}ppi.typ"
        png_path = self.cache_directory / f"{name}@{ppi}ppi.png"

        typ_path.write_text(
            "#set page("
            "width: auto, height: auto, "
            f"margin: {self.padding_pt}pt, fill: none"
            ")\n"
            "#set text(size: 12pt, fill: white)\n"
            f"#set math.frac(style: \"{"horizontal" if frac_inline else "skewed"}\")\n"
            f"{formula}\n",
            encoding="utf-8",
        )

        try:
            process = subprocess.run(
                [
                    "typst",
                    "compile",
                    str(typ_path),
                    str(png_path),
                    "--ppi",
                    str(ppi),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError as error:
            return FormulaResult(
                name=name,
                png_path=png_path,
                success=False,
                return_code=-1,
                stdout="",
                stderr=f"Typst was not found: {error}",
            )
        except subprocess.TimeoutExpired as error:
            return FormulaResult(
                name=name,
                png_path=png_path,
                success=False,
                return_code=-1,
                stdout=error.stdout or "", # type: ignore
                stderr=f"Typst timed out: {error.stderr or ''}",
            )

        return FormulaResult(
            name=name,
            png_path=png_path,
            success=process.returncode == 0 and png_path.is_file(),
            return_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    def queue_formula(
        self,
        name: str,
        formula: str,
        ppi: int,
        frac_inline: bool = True
    ) -> Future[FormulaResult]:
        existing = self.pending.get(name)
        if existing is not None:
            return existing

        future = self.executor.submit(
            self.compile_formula,
            formula,
            name,
            ppi,
            frac_inline=frac_inline
        )
        self.pending[name] = future
        return future

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

    def __enter__(self) -> "TypstFormulaRenderer":
        return self

    def __exit__(self, *_: object) -> None:
        self.shutdown()
