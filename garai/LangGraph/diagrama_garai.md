---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	garai_node(garai_node)
	nodo_herramientas(nodo_herramientas)
	__end__([<p>__end__</p>]):::last
	__start__ --> garai_node;
	garai_node -.-> __end__;
	garai_node -.-> nodo_herramientas;
	nodo_herramientas --> garai_node;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
