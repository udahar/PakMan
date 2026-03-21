#!/usr/bin/env python3
"""
Tool Composer - Drag-and-Drop Agent Builder
Starter implementation
"""

import streamlit as st
import json
from abc import ABC, abstractmethod
from typing import Any


class Node(ABC):
    name: str = "BaseNode"
    inputs: list = []
    outputs: list = []
    
    @abstractmethod
    def process(self, inputs: dict) -> dict:
        pass


class LLMNode(Node):
    name = "LLM"
    inputs = ["prompt"]
    outputs = ["response"]
    
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        
    def process(self, inputs: dict) -> dict:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=self.model)
        response = llm.invoke(inputs.get("prompt", ""))
        return {"response": response.content}


class BashNode(Node):
    name = "Bash"
    inputs = ["command"]
    outputs = ["output"]
    
    def process(self, inputs: dict) -> dict:
        import subprocess
        result = subprocess.run(
            inputs.get("command", ""),
            shell=True,
            capture_output=True,
            text=True
        )
        return {"output": result.stdout or result.stderr}


class FilterNode(Node):
    name = "Filter"
    inputs = ["data"]
    outputs = ["filtered"]
    
    def __init__(self, condition: str):
        self.condition = condition
        
    def process(self, inputs: dict) -> dict:
        # Simple filter - pass through for now
        return {"filtered": inputs.get("data", "")}


# Node Registry
NODE_REGISTRY = {
    "llm": LLMNode,
    "bash": BashNode,
    "filter": FilterNode,
}


class FlowEngine:
    def __init__(self, pipeline: dict):
        self.pipeline = pipeline
        self.nodes = {}
        
    def build(self):
        """Instantiate nodes from pipeline"""
        for node_id, node_data in self.pipeline.get("nodes", {}).items():
            node_type = node_data.get("type")
            if node_type in NODE_REGISTRY:
                self.nodes[node_id] = NODE_REGISTRY[node_type](                
    def run(self)
, initial_inputs: dict) -> dict:
        """Execute pipeline"""
        self.build()
        state = initial_inputs.copy()
        
        # Simple topological sort - run in order
        for node_id, node_data in self.pipeline.get("nodes", {}).items():
            node = self.nodes.get(node_id)
            if node:
                node_inputs = {}
                for inp in node.inputs:
                    # Get from state or edges
                    if inp in state:
                        node_inputs[inp] = state[inp]
                        
                result = node.process(node_inputs)
                state.update(result)
                
        return state


# Streamlit UI
def main():
    st.title("Tool Composer")
    
    # Sidebar - Node palette
    with st.sidebar:
        st.header("Node Palette")
        selected_node = st.selectbox(
            "Add Node",
            list(NODE_REGISTRY.keys())
        )
        
        if st.button("Add Node"):
            st.session_state.nodes = st.session_state.get("nodes", [])
            st.session_state.nodes.append({"type": selected_node, "id": len(st.session_state.nodes)})
            
    # Main area - Canvas
    st.header("Canvas")
    
    if "nodes" not in st.session_state:
        st.session_state.nodes = []
        
    for node in st.session_state.nodes:
        st.text_input(f"Node {node['id']}", value=node["type"], disabled=True)
        
    # Pipeline JSON
    st.header("Pipeline JSON")
    pipeline = {"nodes": {str(n["id"]): {"type": n["type"]} for n in st.session_state.nodes}}
    st.json(pipeline)
    
    # Run button
    if st.button("Run Pipeline"):
        engine = FlowEngine(pipeline)
        result = engine.run({"prompt": "Hello"})
        st.success(f"Result: {result}")


if __name__ == "__main__":
    main()
