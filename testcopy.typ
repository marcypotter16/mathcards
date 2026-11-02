#set page(width: auto, height: auto, margin: 10pt, fill: rgb("#ffffff"))

// MODIFICA: Ora la macro misura il body visivo *prima* di creare il metadato,
// così possiamo salvare le dimensioni reali direttamente al momento dell'ispezione!
#let target(id, body) = context [
  #body
  #metadata((
    width: measure(body).width / 1pt,
    height: measure(body).height / 1pt
  ))#label(id)
]

// Formula minimale di test
$
  #target("l_0", [$A$])
  stretch(->, size: #200%)
  #target("r_0", [$B$])
$

// Blocco di introspezione aggiornato
#context [
  #metadata({
    let positions = (:)
    for i in range(5) {
      let selectors = (
        "l_" + str(i): label("l_" + str(i)),
        "r_" + str(i): label("r_" + str(i))
      )
      for (key, sel) in selectors {
        let matches = query(sel)
        if matches.len() > 0 {
          let elem = matches.first()
          let pos = elem.location().position()
          
          // Recuperiamo larghezza e altezza salvate precedentemente dentro il 'value' del metadato
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
