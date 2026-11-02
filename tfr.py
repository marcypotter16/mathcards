import json
from re import search
import subprocess
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_DNS, uuid5


@dataclass(frozen=True)
class FormulaResult:
    name: str
    png_path: Path
    success: bool
    return_code: int
    stdout: str
    stderr: str
    # Mantiene le coordinate esatte (x, y, width, height) in punti (pt) per ogni elemento tracciato
    layout_data: dict[str, dict[str, float]] = field(default_factory=dict)


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
        frac_inline: bool = True,
        query_block: str | None = None,  # Accetta direttamente l'intero blocco magico Typst
    ) -> FormulaResult:
        self.cache_directory.mkdir(parents=True, exist_ok=True)

        typ_path = self.cache_directory / f"{name}@{ppi}ppi.typ"
        png_path = self.cache_directory / f"{name}@{ppi}ppi.png"

        # 1. Configurazione della testata fissa
        header = (
            "#set page("
            "width: auto, height: auto, "
            f"margin: {self.padding_pt}pt, fill: none"
            ")\n"
            "#set text(size: 12pt, fill: white)\n"
            f"#set math.frac(style: \"{'horizontal' if frac_inline else 'skewed'}\")\n\n"
        )

        # Se viene passato un blocco di query, definiamo anche la macro di target in cima per comodità
        if query_block:
            header += (
                "// Macro generata per tracciare la geometria esatta dei singoli elementi\n"
                "#let target(id, body) = context [\n"
                "  #body\n"
                "  #metadata((\n"
                "    width: measure(body).width / 1pt,\n"
                "    height: measure(body).height / 1pt\n"
                "  ))#label(id)\n"
                "]\n\n"
            )

        # Se c'è un blocco magico, lo appendiamo in fondo
        footer = f"\n{query_block}\n" if query_block else ""

        typst_code = f"{header}{formula}{footer}"
        typ_path.write_text(typst_code, encoding="utf-8")

        try:
            # 2. Compilazione dell'immagine PNG
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
                stdout=error.stdout or "",  # type: ignore
                stderr=f"Typst timed out: {error.stderr or ''}",
            )

        # 3. Estrazione dei dati (Solo se l'utente ha iniettato un blocco magico e la compilazione è riuscita)
        layout_data = {}
        query_json: list[dict[str, Any]]
        if query_block and process.returncode == 0 and png_path.is_file():
            # Estraggo automaticamente il nome della label dal blocco magico usando una regex (es: <layout_data> -> layout_data)
            label_match = search(r"<([a-zA-Z0-9_-]+)>", query_block)

            if label_match:
                label_name = label_match.group(1)
                try:
                    query_process = subprocess.run(
                        [
                            "typst",
                            "query",
                            str(typ_path),
                            f"<{label_name}>",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if (
                        query_process.returncode == 0
                        and query_process.stdout.strip()
                    ):
                        query_json = json.loads(query_process.stdout)
                        if (
                            isinstance(query_json, list)
                            and len(query_json) > 0
                        ):
                            layout_data = query_json[0].get("value", {})
                except Exception:
                    layout_data = {}

        return FormulaResult(
            name=name,
            png_path=png_path,
            success=process.returncode == 0 and png_path.is_file(),
            return_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            layout_data=layout_data,
        )

    def queue_formula(
        self, formula: str, ppi: int, frac_inline: bool = True, query_block: str | None = None
    ) -> Future[FormulaResult]:
        name = str(uuid5(NAMESPACE_DNS, formula + str(ppi)))
        existing = self.pending.get(name)
        if existing is not None:
            return existing

        future = self.executor.submit(
            self.compile_formula, formula, name, ppi, frac_inline=frac_inline, query_block=query_block
        )
        self.pending[name] = future
        return future

    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)

    def __enter__(self) -> "TypstFormulaRenderer":
        return self

    def __exit__(self, *_: object) -> None:
        self.shutdown()
