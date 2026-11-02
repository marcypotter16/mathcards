#set page(width: auto, height: auto, margin: 1.0pt, fill: none)
#set text(size: 12pt, fill: white)
#set math.frac(style: "horizontal")


                #let target(id, body) = context {
                let m = measure(body)
                box(
                    width: m.width, height: m.height,
                    place(top + left, body),
                    place(top + left, metadata((
                    width:  m.width  / 1pt,
                    height: m.height / 1pt,
                    ))label(id))
                )
                }
            $ mat(delim: #none,
  frac(ZZ_(5)[x], (x^3 + 2 x + 4)), stretch(->, size: #250%), (ZZ_(5) [x]);
  #target("l_0", $1$), stretch(|->, size: #250%), #target("r_0", $?$);;
  #target("l_1", $x$), stretch(|->, size: #250%), #target("r_1", $?$);;
  #target("l_2", $x^2$), stretch(|->, size: #250%), #target("r_2", $?$);;
) $


            #context [
            #metadata({
                let positions = (:)
                for i in range(50) {
                let selectors = (
                    "l_" + str(i): label("l_" + str(i)),
                    "r_" + str(i): label("r_" + str(i))
                )
                for (key, sel) in selectors {
                    let matches = query(sel)
                    if matches.len() > 0 {
                    let elem = matches.first()
                    let pos = elem.location().position()
                    let size = elem.value
                    positions.insert(key, (
                        x: pos.x / 1pt,
                        y: pos.y / 1pt,
                        width: size.width,
                        height: size.height
                    ))
                    }
                }
                }
                positions
            })<layout_data>
            ]