"""
Streamlit GUI for profit-solver with tabs for configuration, execution, and results.
"""

import streamlit as st
import json
import time
import psutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

from src.solver.data import load_data, DataBundle
from src.solver.domain import ProductState
from src.solver.search import search_with_strategy, compute_profit
from src.solver.persist import with_run


def init_session_state():
    """Initialize session state variables."""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'search_in_progress' not in st.session_state:
        st.session_state.search_in_progress = False
    if 'run_metrics' not in st.session_state:
        st.session_state.run_metrics = {}
    if 'data_bundle' not in st.session_state:
        st.session_state.data_bundle = None
    if 'constraints' not in st.session_state:
        st.session_state.constraints = {}


def run_tab():
    """Run configuration and execution tab."""
    st.header("🚀 Run Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        K = st.number_input("Target Depth (K)", min_value=1, max_value=20, value=3, 
                           help="Maximum depth for search tree")
        base_product = st.text_input("Base Product Type", value="potion",
                                     help="Starting product type")
        strategy = st.selectbox("Search Strategy", 
                               options=["exhaustive", "bb", "beam"],
                               format_func=lambda x: {
                                   "exhaustive": "Exhaustive Search",
                                   "bb": "Branch-and-Bound",
                                   "beam": "Beam Search"
                               }[x],
                               help="Search algorithm to use")
    
    with col2:
        beam_width = st.number_input("Beam Width", min_value=1, max_value=100, value=10,
                                    disabled=(strategy != "beam"),
                                    help="Number of states to keep per layer (beam search only)")
        time_limit = st.number_input("Time Limit (seconds)", min_value=0.0, value=0.0, step=0.1,
                                    help="Maximum execution time (0 = unlimited)")
        storage_mode = st.radio("Storage Mode", 
                               options=["in-memory", "sqlite"],
                               horizontal=True,
                               help="Data storage backend")
    
    st.divider()
    
    col_start, col_resume = st.columns(2)
    
    with col_start:
        if st.button("▶️ Start Search", type="primary", disabled=st.session_state.data_bundle is None):
            if st.session_state.data_bundle is None:
                st.error("Please load data in the Data tab first")
            else:
                run_search(K, base_product, strategy, beam_width, 
                          time_limit if time_limit > 0 else None, storage_mode)
    
    with col_resume:
        if st.button("🔄 Resume from Checkpoint", disabled=True):
            st.info("Resume functionality coming soon")
    
    # Show search progress
    if st.session_state.search_in_progress:
        with st.spinner("Search in progress..."):
            st.info("Search is running. Please wait...")
    
    # Display results summary
    if st.session_state.search_results:
        st.success("✅ Search completed!")
        results = st.session_state.search_results
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Terminal States", results.get('terminal_states_count', 0))
        with col2:
            st.metric("Time Elapsed", f"{results.get('elapsed_time', 0):.3f}s")
        with col3:
            status = "⚠️ Timeout" if results.get('timed_out') else "✅ Complete"
            st.metric("Status", status)


def run_search(K: int, base_product: str, strategy: str, beam_width: int, 
               time_limit: Optional[float], storage_mode: str):
    """Execute the search."""
    st.session_state.search_in_progress = True
    
    try:
        data = st.session_state.data_bundle
        base = ProductState(product_type=base_product)
        ingredients = list(data.ingredient_costs.keys())
        constraints = st.session_state.constraints
        
        start_time = time.time()
        best_state, terminal_states, timed_out = search_with_strategy(
            strategy, base, K, ingredients, data, constraints, 
            beam_width=beam_width, time_limit=time_limit
        )
        elapsed = time.time() - start_time
        
        # Store results
        st.session_state.search_results = {
            'best_state': best_state,
            'terminal_states': terminal_states,
            'timed_out': timed_out,
            'terminal_states_count': len(terminal_states),
            'elapsed_time': elapsed,
            'strategy': strategy,
            'K': K,
            'base_product': base_product
        }
        
        # Update metrics
        st.session_state.run_metrics = {
            'start_time': start_time,
            'end_time': time.time(),
            'duration': elapsed,
            'states_explored': len(terminal_states),
            'memory_used_mb': psutil.Process().memory_info().rss / 1024 / 1024
        }
        
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
    finally:
        st.session_state.search_in_progress = False


def constraints_tab():
    """Constraints configuration tab."""
    st.header("⚙️ Constraints")
    
    st.markdown("Configure constraints for the search:")
    
    budget_enabled = st.checkbox("Enable Budget Constraint")
    if budget_enabled:
        budget = st.number_input("Maximum Budget", min_value=0.0, value=10.0, step=0.1)
        st.session_state.constraints['budget_max'] = budget
    else:
        st.session_state.constraints.pop('budget_max', None)
    
    st.divider()
    
    max_repeats_enabled = st.checkbox("Enable Max Repeats Constraint")
    if max_repeats_enabled:
        max_repeats = st.number_input("Max Ingredient Repeats", min_value=1, value=3)
        st.session_state.constraints['max_repeats'] = max_repeats
    else:
        st.session_state.constraints.pop('max_repeats', None)
    
    st.divider()
    
    st.subheader("Required Effects")
    required_effects = st.text_area("Required effects (one per line)", 
                                   help="Effects that must be present in the final product")
    if required_effects.strip():
        st.session_state.constraints['required_effects'] = [
            e.strip() for e in required_effects.split('\n') if e.strip()
        ]
    else:
        st.session_state.constraints.pop('required_effects', None)
    
    st.divider()
    
    st.subheader("Forbidden Effects")
    forbidden_effects = st.text_area("Forbidden effects (one per line)",
                                    help="Effects that must NOT be present in the final product")
    if forbidden_effects.strip():
        st.session_state.constraints['forbidden_effects'] = [
            e.strip() for e in forbidden_effects.split('\n') if e.strip()
        ]
    else:
        st.session_state.constraints.pop('forbidden_effects', None)
    
    # Display current constraints
    if st.session_state.constraints:
        st.divider()
        st.subheader("Active Constraints")
        st.json(st.session_state.constraints)
    else:
        st.info("No constraints currently active")


def data_tab():
    """Data loading and preview tab."""
    st.header("📊 Data Management")
    
    # File picker
    data_dir = Path("data")
    if data_dir.exists():
        data_files = list(data_dir.glob("*.json"))
        if data_files:
            file_names = [f.name for f in data_files]
            selected_file = st.selectbox("Select Data File", file_names)
            
            if st.button("📂 Load Data"):
                try:
                    data_path = data_dir / selected_file
                    data = load_data(str(data_path))
                    st.session_state.data_bundle = data
                    st.success(f"✅ Loaded data from {selected_file}")
                except Exception as e:
                    st.error(f"Failed to load data: {str(e)}")
        else:
            st.warning("No data files found in 'data/' directory")
    else:
        st.error("Data directory not found")
    
    # File upload
    st.divider()
    st.subheader("Upload New Data")
    uploaded_file = st.file_uploader("Upload JSON data file", type=['json'])
    if uploaded_file:
        try:
            content = uploaded_file.read().decode('utf-8')
            obj = json.loads(content)
            
            # Validate structure
            required_keys = ['BASE_PRICES', 'EFFECT_MULTIPLIERS', 'INGREDIENT_COSTS', 'RULES', 'PRODUCTION_COSTS']
            missing = [k for k in required_keys if k not in obj]
            
            if missing:
                st.error(f"Missing required keys: {', '.join(missing)}")
            else:
                st.success("✅ Valid data structure")
                
                # Save and load
                if st.button("💾 Save and Load"):
                    save_path = data_dir / uploaded_file.name
                    save_path.write_text(content, encoding='utf-8')
                    st.session_state.data_bundle = load_data(str(save_path))
                    st.success(f"Saved and loaded {uploaded_file.name}")
                    st.rerun()
        except Exception as e:
            st.error(f"Invalid JSON: {str(e)}")
    
    # Preview loaded data
    if st.session_state.data_bundle:
        st.divider()
        st.subheader("📋 Data Preview")
        
        data = st.session_state.data_bundle
        
        tab1, tab2, tab3, tab4 = st.tabs(["Base Prices", "Effect Multipliers", "Ingredient Costs", "Rules"])
        
        with tab1:
            st.dataframe(pd.DataFrame([
                {"Product": k, "Base Price": v} 
                for k, v in data.base_prices.items()
            ]))
        
        with tab2:
            st.dataframe(pd.DataFrame([
                {"Effect": k, "Multiplier": v}
                for k, v in data.effect_multipliers.items()
            ]))
        
        with tab3:
            st.dataframe(pd.DataFrame([
                {"Ingredient": k, "Cost": v}
                for k, v in data.ingredient_costs.items()
            ]))
        
        with tab4:
            st.json(data.rules)


def diagnostics_tab():
    """Diagnostics and monitoring tab."""
    st.header("🔍 Diagnostics")
    
    # System metrics
    st.subheader("System Metrics")
    col1, col2, col3 = st.columns(3)
    
    process = psutil.Process()
    
    with col1:
        memory_mb = process.memory_info().rss / 1024 / 1024
        st.metric("Memory Usage", f"{memory_mb:.2f} MB")
    
    with col2:
        cpu_percent = process.cpu_percent(interval=0.1)
        st.metric("CPU Usage", f"{cpu_percent:.1f}%")
    
    with col3:
        # Check runs directory size
        runs_dir = Path("runs")
        if runs_dir.exists():
            runs_size = sum(f.stat().st_size for f in runs_dir.glob("**/*") if f.is_file())
            runs_size_mb = runs_size / 1024 / 1024
            st.metric("Runs Directory", f"{runs_size_mb:.2f} MB")
        else:
            st.metric("Runs Directory", "N/A")
    
    # Run metrics
    if st.session_state.run_metrics:
        st.divider()
        st.subheader("Last Run Metrics")
        
        metrics = st.session_state.run_metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Duration", f"{metrics.get('duration', 0):.3f}s")
            st.metric("States Explored", metrics.get('states_explored', 0))
        
        with col2:
            st.metric("Start Time", time.strftime('%H:%M:%S', time.localtime(metrics.get('start_time', 0))))
            st.metric("Memory Used", f"{metrics.get('memory_used_mb', 0):.2f} MB")
    
    # Checkpoints
    st.divider()
    st.subheader("Checkpoints")
    
    runs_dir = Path("runs")
    if runs_dir.exists():
        checkpoints = list(runs_dir.glob("checkpoint_*.json"))
        if checkpoints:
            for cp in sorted(checkpoints, reverse=True)[:5]:
                with st.expander(f"📄 {cp.name}"):
                    try:
                        data = json.loads(cp.read_text())
                        st.json(data)
                    except Exception as e:
                        st.error(f"Failed to read checkpoint: {e}")
        else:
            st.info("No checkpoints found")
    else:
        st.info("Runs directory does not exist")


def outputs_tab():
    """Results and outputs tab."""
    st.header("📈 Outputs")
    
    if not st.session_state.search_results:
        st.info("No search results available. Run a search in the Run tab.")
        return
    
    results = st.session_state.search_results
    best_state = results.get('best_state')
    terminal_states = results.get('terminal_states', [])
    
    if not best_state:
        st.warning("Search completed but no solution found")
        return
    
    # Best solution card
    st.subheader("🏆 Best Solution")
    
    data = st.session_state.data_bundle
    profit = compute_profit(best_state, data)
    
    from src.solver.valuation import sale_value
    valuation = sale_value(best_state.product_type, best_state.effects, 
                          data.base_prices, data.effect_multipliers)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Profit", f"${profit:.2f}")
    with col2:
        st.metric("Sale Value", f"${valuation.sale_value:.2f}")
    with col3:
        st.metric("Total Cost", f"${best_state.cost_so_far:.2f}")
    with col4:
        st.metric("Depth", best_state.depth)
    
    # Path visualization
    st.markdown("**Path:**")
    if best_state.path:
        path_str = " → ".join(best_state.path)
        st.code(path_str)
    else:
        st.text("(base product)")
    
    # Effects
    st.markdown("**Effects:**")
    if best_state.effects:
        st.write(", ".join(best_state.effects))
    else:
        st.text("(no effects)")
    
    # Breakdown
    with st.expander("💰 Value Breakdown"):
        st.write(f"Base Price: ${valuation.base_price:.2f}")
        st.write(f"Multiplier: {valuation.multiplier_product:.2f}x")
        st.write(f"Sale Value: ${valuation.sale_value:.2f}")
        st.write(f"Cost: ${best_state.cost_so_far:.2f}")
        st.write(f"**Profit: ${profit:.2f}**")
    
    st.divider()
    
    # Top-M results table
    st.subheader("📊 Top Solutions")
    
    if terminal_states:
        # Calculate profits for all states
        state_data = []
        for state in terminal_states:
            profit_val = compute_profit(state, data)
            state_data.append({
                'Path': ' → '.join(state.path) if state.path else '(base)',
                'Effects': ', '.join(state.effects) if state.effects else '(none)',
                'Cost': state.cost_so_far,
                'Profit': profit_val,
                'Depth': state.depth
            })
        
        # Sort by profit descending
        state_data.sort(key=lambda x: x['Profit'], reverse=True)
        
        # Show top 10
        top_m = st.slider("Number of solutions to display", 1, min(50, len(state_data)), 10)
        df = pd.DataFrame(state_data[:top_m])
        st.dataframe(df, use_container_width=True)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "top_solutions.csv", "text/csv")
        
        with col2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button("📥 Download JSON", json_data, "top_solutions.json", "application/json")
    
    # Layer statistics
    st.divider()
    st.subheader("📉 Layer Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Terminal States", len(terminal_states))
    with col2:
        st.metric("Search Strategy", results.get('strategy', 'N/A').upper())
    with col3:
        st.metric("Target Depth", results.get('K', 'N/A'))


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Profit Solver",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("💰 Profit Solver")
    st.markdown("Search-based profit maximization engine with configurable strategies")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        st.markdown("Use the tabs below to configure and run searches")
        
        st.divider()
        
        st.header("Quick Info")
        if st.session_state.data_bundle:
            st.success("✅ Data loaded")
        else:
            st.warning("⚠️ No data loaded")
        
        if st.session_state.search_results:
            st.success("✅ Results available")
        else:
            st.info("ℹ️ No results yet")
        
        st.divider()
        
        st.markdown("### About")
        st.markdown("Profit Solver implements exhaustive, branch-and-bound, and beam search strategies for optimal product configuration.")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚀 Run", 
        "⚙️ Constraints", 
        "📊 Data", 
        "🔍 Diagnostics", 
        "📈 Outputs"
    ])
    
    with tab1:
        run_tab()
    
    with tab2:
        constraints_tab()
    
    with tab3:
        data_tab()
    
    with tab4:
        diagnostics_tab()
    
    with tab5:
        outputs_tab()


if __name__ == "__main__":
    main()
