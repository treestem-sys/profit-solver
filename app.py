"""Streamlit web application for the profit solver.

This app provides an interactive UI for:
- Uploading problem specifications
- Configuring search parameters and constraints
- Running the solver and viewing results
- Analyzing solution quality and search performance
"""

import json
from pathlib import Path

import streamlit as st

from src.solver import Problem, greedy_search, load_data, save_solution

# Page configuration
st.set_page_config(
    page_title="Profit Solver",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💰 Profit Solver")
st.markdown("**Search-based profit maximization engine**")

# Sidebar for configuration
st.sidebar.header("Configuration")

# File upload or selection
st.sidebar.subheader("Data Specification")
uploaded_file = st.sidebar.file_uploader("Upload spec.json", type=["json"])

if uploaded_file is not None:
    spec_data = json.load(uploaded_file)
    st.sidebar.success("Spec uploaded successfully!")
else:
    # Use default spec
    default_spec_path = Path("data/spec.json")
    if default_spec_path.exists():
        spec_data = json.loads(default_spec_path.read_text())
        st.sidebar.info("Using default data/spec.json")
    else:
        st.sidebar.warning("No spec file found. Please upload one.")
        spec_data = None

# Main content area
if spec_data is not None:
    # Display spec preview
    with st.expander("📋 View Data Specification", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Base Prices")
            st.json(spec_data.get("BASE_PRICES", {}))

            st.subheader("Ingredient Costs")
            st.json(spec_data.get("INGREDIENT_COSTS", {}))

        with col2:
            st.subheader("Effect Multipliers")
            st.json(spec_data.get("EFFECT_MULTIPLIERS", {}))

            st.subheader("Production Costs")
            st.json(spec_data.get("PRODUCTION_COSTS", {}))

    # Problem configuration
    st.header("🎯 Problem Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        product_types = list(spec_data.get("BASE_PRICES", {}).keys())
        if product_types:
            product_type = st.selectbox("Product Type", product_types)
        else:
            product_type = st.text_input("Product Type", value="potion")

    with col2:
        max_depth = st.number_input("Max Depth (K)", min_value=1, max_value=10, value=3)

    with col3:
        budget_max = st.number_input("Budget Limit", min_value=0.0, value=100.0, step=1.0)

    # Run solver
    st.header("🚀 Run Solver")

    if st.button("Run Greedy Search", type="primary"):
        with st.spinner("Running greedy search..."):
            # Save uploaded spec temporarily if needed
            temp_spec_path = Path("/tmp/temp_spec.json")
            temp_spec_path.write_text(json.dumps(spec_data))

            # Load data and create problem
            data = load_data(temp_spec_path)
            constraints = {"budget_max": budget_max} if budget_max > 0 else None
            problem = Problem(
                product_type=product_type,
                max_depth=int(max_depth),
                data=data,
                constraints=constraints
            )

            # Run search
            solutions = list(greedy_search(problem))

            if solutions:
                # Find best solution
                best_solution = max(solutions, key=lambda s: s.profit)

                st.success(f"Found {len(solutions)} solutions!")

                # Display best solution
                st.header("🏆 Best Solution")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Profit", f"${best_solution.profit:.2f}")
                with col2:
                    st.metric("Sale Value", f"${best_solution.sale_value:.2f}")
                with col3:
                    st.metric("Total Cost", f"${best_solution.total_cost:.2f}")
                with col4:
                    st.metric("Depth", best_solution.state.depth)

                # Solution details
                st.subheader("Solution Details")
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Ingredient Path:**")
                    for i, ingredient in enumerate(best_solution.state.path, 1):
                        st.write(f"{i}. {ingredient}")

                with col2:
                    st.write("**Effects Applied:**")
                    for effect in best_solution.state.effects:
                        st.write(f"• {effect}")

                # Save solution
                output_path = Path("/tmp/best_solution.json")
                save_solution(output_path, best_solution)

                with open(output_path) as f:
                    solution_json = f.read()

                st.download_button(
                    label="💾 Download Solution",
                    data=solution_json,
                    file_name="solution.json",
                    mime="application/json"
                )

                # All solutions table
                with st.expander("📊 View All Solutions", expanded=False):
                    solutions_data = []
                    for i, sol in enumerate(sorted(solutions, key=lambda s: s.profit, reverse=True), 1):
                        solutions_data.append({
                            "Rank": i,
                            "Profit": f"${sol.profit:.2f}",
                            "Sale Value": f"${sol.sale_value:.2f}",
                            "Cost": f"${sol.total_cost:.2f}",
                            "Path": " → ".join(sol.state.path),
                            "Effects": ", ".join(sol.state.effects)
                        })

                    st.table(solutions_data[:20])  # Show top 20
                    st.info(f"Showing top 20 of {len(solutions)} solutions")
            else:
                st.error("No solutions found! Try adjusting constraints.")

    # Help section
    with st.expander("ℹ️ Help & Instructions", expanded=False):
        st.markdown("""
        ### How to Use

        1. **Upload Specification**: Upload your data spec JSON or use the default
        2. **Configure Problem**: Select product type, max depth, and budget
        3. **Run Search**: Click "Run Greedy Search" to find optimal solutions
        4. **View Results**: See the best solution and download results

        ### Data Specification Format

        Your JSON file should contain:
        - `BASE_PRICES`: Product type → base price mapping
        - `EFFECT_MULTIPLIERS`: Effect name → multiplier mapping
        - `INGREDIENT_COSTS`: Ingredient name → cost mapping
        - `RULES`: Ingredient → effect rules mapping
        - `PRODUCTION_COSTS`: Fixed and per-ingredient production costs

        ### TODO Features

        - [ ] Support for multiple search strategies (beam search, branch-and-bound)
        - [ ] Real-time progress updates during search
        - [ ] Resume from checkpoint
        - [ ] Advanced constraint configuration
        - [ ] Visualization of search tree
        - [ ] Comparison of multiple runs
        """)

else:
    st.warning("Please upload a data specification file to get started.")
    st.info("Upload a JSON file with BASE_PRICES, EFFECT_MULTIPLIERS, INGREDIENT_COSTS, RULES, and PRODUCTION_COSTS.")
