"""
Tool Composer Streamlit UI

Visual interface for building and executing AI pipelines.
"""

import streamlit as st
import json
from datetime import datetime

from toolcomposer.models import PipelineConfig, NodeConfig, EdgeConfig
from toolcomposer.flow_engine import FlowEngine
from toolcomposer.serializer import PipelineSerializer
from toolcomposer.node_registry import get_available_nodes


def init_session_state():
    """Initialize session state variables."""
    if "nodes" not in st.session_state:
        st.session_state.nodes = []
    if "edges" not in st.session_state:
        st.session_state.edges = []
    if "pipeline_name" not in st.session_state:
        st.session_state.pipeline_name = "My Pipeline"
    if "pipeline_description" not in st.session_state:
        st.session_state.pipeline_description = ""
    if "last_result" not in st.session_state:
        st.session_state.last_result = None


def render_node_palette():
    """Render the node palette sidebar."""
    st.sidebar.header("Node Palette")

    available_nodes = get_available_nodes()
    categories = set(node["category"] for node in available_nodes)

    selected_node = None

    for category in sorted(categories):
        with st.sidebar.expander(category.upper(), expanded=False):
            category_nodes = [
                n for n in available_nodes if n["category"] == category
            ]

            for node in category_nodes:
                if st.button(
                    f"{node['name']}",
                    key=f"add_{node['type']}",
                    help=node.get("description", ""),
                ):
                    selected_node = node

    return selected_node


def render_canvas():
    """Render the main canvas area."""
    st.header("Canvas")

    if not st.session_state.nodes:
        st.info("Add nodes from the palette to get started")
        return

    # Display nodes
    for i, node in enumerate(st.session_state.nodes):
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.text_input(
                    "Name",
                    value=node.get("name", node["type"]),
                    key=f"node_name_{i}",
                    label_visibility="collapsed",
                )

            with col2:
                st.text(node["type"])

            with col3:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.nodes.pop(i)
                    st.rerun()

            # Node parameters
            with st.expander("Parameters"):
                node_types = get_available_nodes()
                node_info = next(
                    (n for n in node_types if n["type"] == node["type"]), None
                )

                if node_info:
                    st.text(f"Inputs: {', '.join(node_info['inputs'])}")
                    st.text(f"Outputs: {', '.join(node_info['outputs'])}")

                # Edit parameters
                params = node.get("parameters", {})
                for key, value in params.items():
                    new_value = st.text_input(
                        key, value=value, key=f"param_{i}_{key}"
                    )
                    params[key] = new_value

                # Add new parameter
                new_param_key = st.text_input("New parameter key", key=f"newkey_{i}")
                if new_param_key:
                    new_param_value = st.text_input(
                        "Value", value="", key=f"newval_{i}"
                    )
                    if st.button("Add", key=f"addparam_{i}"):
                        params[new_param_key] = new_param_value
                        st.rerun()

                node["parameters"] = params


def render_pipeline_json():
    """Render the pipeline JSON preview."""
    st.header("Pipeline JSON")

    pipeline = build_pipeline_config()
    serializer = PipelineSerializer()

    try:
        json_str = serializer.to_json(pipeline)
        st.code(json_str, language="json")

        # Download button
        st.download_button(
            label="📥 Download Pipeline",
            data=json_str,
            file_name=f"{pipeline.name.replace(' ', '_')}.json",
            mime="application/json",
        )
    except Exception as e:
        st.error(f"Failed to generate JSON: {e}")


def build_pipeline_config() -> PipelineConfig:
    """Build PipelineConfig from session state."""
    nodes = []
    for i, node_data in enumerate(st.session_state.nodes):
        node_config = NodeConfig(
            id=node_data.get("id", f"node_{i}"),
            type=node_data["type"],
            name=node_data.get("name", node_data["type"]),
            parameters=node_data.get("parameters", {}),
        )
        nodes.append(node_config)

    edges = []
    for i, edge_data in enumerate(st.session_state.edges):
        edge_config = EdgeConfig(
            id=edge_data.get("id", f"edge_{i}"),
            source_node=edge_data["source"],
            target_node=edge_data["target"],
        )
        edges.append(edge_config)

    return PipelineConfig(
        id="pipeline_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        name=st.session_state.pipeline_name,
        description=st.session_state.pipeline_description,
        nodes=nodes,
        edges=edges,
    )


def run_pipeline(pipeline: PipelineConfig, inputs: dict) -> dict:
    """Execute a pipeline."""
    engine = FlowEngine(pipeline)
    result = engine.execute(inputs)
    return result.to_dict()


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Tool Composer",
        page_icon="🔧",
        layout="wide",
    )

    st.title("🔧 Tool Composer")
    st.caption("Build AI workflows with drag-and-drop nodes")

    init_session_state()

    # Sidebar
    with st.sidebar:
        st.header("Pipeline Settings")

        st.session_state.pipeline_name = st.text_input(
            "Name", value=st.session_state.pipeline_name
        )
        st.session_state.pipeline_description = st.text_area(
            "Description", value=st.session_state.pipeline_description
        )

        st.divider()

        # Add node button
        selected_node = render_node_palette()

        if selected_node:
            new_node = {
                "type": selected_node["type"],
                "name": selected_node["name"],
                "parameters": {},
                "id": f"node_{len(st.session_state.nodes)}",
            }
            st.session_state.nodes.append(new_node)
            st.rerun()

        st.divider()

        # Load/Save
        uploaded_file = st.file_uploader("Load Pipeline", type=["json"])
        if uploaded_file:
            try:
                json_data = json.loads(uploaded_file.read())
                serializer = PipelineSerializer()
                pipeline = serializer.from_json(json.dumps(json_data))

                st.session_state.nodes = [n.to_dict() for n in pipeline.nodes]
                st.session_state.edges = [e.to_dict() for e in pipeline.edges]
                st.session_state.pipeline_name = pipeline.name
                st.session_state.pipeline_description = pipeline.description

                st.success("Pipeline loaded!")
            except Exception as e:
                st.error(f"Failed to load pipeline: {e}")

    # Main area
    col1, col2 = st.columns(2)

    with col1:
        render_canvas()

    with col2:
        render_pipeline_json()

    # Run section
    st.divider()
    st.header("Execute Pipeline")

    col1, col2 = st.columns([3, 1])

    with col1:
        initial_input = st.text_area(
            "Initial Input (JSON)",
            value='{"prompt": "Hello"}',
            help="Initial input to pass to the pipeline",
        )

    with col2:
        if st.button("▶️ Run Pipeline", type="primary", use_container_width=True):
            try:
                pipeline = build_pipeline_config()
                inputs = json.loads(initial_input)

                with st.spinner("Running pipeline..."):
                    result = run_pipeline(pipeline, inputs)

                st.session_state.last_result = result

                if result["success"]:
                    st.success("Pipeline executed successfully!")
                else:
                    st.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")

            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON input: {e}")
            except Exception as e:
                st.error(f"Execution failed: {e}")

    # Results
    if st.session_state.last_result:
        st.divider()
        st.header("Results")

        result = st.session_state.last_result

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Node Results")
            for node_result in result.get("node_results", []):
                status_emoji = "✅" if node_result["status"] == "completed" else "❌"
                st.text(
                    f"{status_emoji} {node_result['node_id']}: {node_result['status']}"
                )

        with col2:
            st.subheader("Summary")
            st.metric("Duration", f"{result.get('duration_ms', 0):.0f}ms")
            st.metric("Nodes", len(result.get("node_results", [])))
            st.metric("Success", result.get("success", False))

        # Final output
        if result.get("final_output"):
            st.subheader("Final Output")
            if isinstance(result["final_output"], dict):
                st.json(result["final_output"])
            else:
                st.text(str(result["final_output"])[:2000])


if __name__ == "__main__":
    main()
