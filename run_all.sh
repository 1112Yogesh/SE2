#!/bin/bash
python cc.py
python cocomo.py
python dfc.py
python halstead.py
python sloc.py

# Generate graphs
python cc_graph.py
python dfc_graph.py
python halstead_graph.py
python sloc_graph.py
