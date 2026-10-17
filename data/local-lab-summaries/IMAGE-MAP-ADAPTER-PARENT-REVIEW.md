# Reviewed image-map discovery adapter

Parent independent review 2026-10-16T05:37:40+00:00: PASS. Only `plan()` differs from641fd9a; every other definition and module statement is AST-identical. The reviewed document-preload and used image-map paths only discover source documents. They cannot execute JavaScript or accept identity/research/redirect/canonical changes.

Actual Yanofsky navigation contains `map name=FrontPageMap`, two reviewed `area href` values and `img usemap=#FrontPageMap`. Exact source/time/SHA/href/map and target URI checks apply; orphan, unused, script/style/comment or ordinary-anchor substitutes fail. Parent239 local tests PASS, including11 new image-map cases,0network. Exact source/test hashes are in the adjacent JSON.
