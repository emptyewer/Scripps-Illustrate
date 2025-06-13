import streamlit as st
import os
import tempfile
from collections import defaultdict
import subprocess

st.set_page_config(page_title="ILLUSTRATE Input File Generator", page_icon=":atom:", layout="wide")

# Add custom CSS for alignment and layout
st.markdown("""
    <style>
    /* Make the app container fill the browser width */
    .stApp {
        max-width: 100%;
        padding: 1rem 2rem;
    }
    /* Make the main container wider */
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* Adjust the form container */
    .form-panel {
        flex: 0.6;
        padding-right: 20px;
        width: 100%;
    }
    /* Adjust the preview container */
    .preview-panel {
        flex: 0.4;
        padding-left: 20px;
        width: 100%;
    }
    .main {
        display: flex;
        flex-direction: row;
        width: 100%;
    }
    .rgb-value {
        padding-top: 0.5rem;
        text-align: left;
    }
    .stTextArea textarea {
        font-family: monospace;
        font-size: 14px;
        line-height: 1.5;
    }
    .st-emotion-cache-16txtl3 {
        font-family: monospace;
    }
    /* Make headers smaller */
    h1 {
        font-size: 1.8rem !important;
    }
    h2 {
        font-size: 1.4rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
    }
    /* Add some spacing between sections */
    .section {
        margin-bottom: 1rem;
    }
    .color-picker-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: -0.5rem;  /* Reduce space between checkbox and color picker */
    }
    </style>
""", unsafe_allow_html=True)

# Standard atomic radii in angstroms (based on covalent radii)
ATOM_SIZES = {
    'C': 1.6,    # Carbon
    'N': 1.5,   # Nitrogen
    'O': 1.5,    # Oxygen
    'S': 1.8,    # Sulfur
    'P': 1.8,    # Phosphorus
    'H': 0.0,    # Hydrogen
    'F': 0.5,    # Fluorine
    'Cl': 1.0,   # Chlorine
    'Br': 1.15,  # Bromine
    'I': 1.4,    # Iodine
    'Na': 1.5,   # Sodium
    'K': 2.0,    # Potassium
    'Ca': 1.8,   # Calcium
    'Mg': 1.5,   # Magnesium
    'Fe': 2.0,   # Iron
    'Zn': 1.2,   # Zinc
    'Cu': 1.2,   # Copper
    'Mn': 1.2,   # Manganese
    'Co': 1.2,   # Cobalt
    'Ni': 1.2,   # Nickel
}

# Add pastel color palettes for different chains
PASTEL_PALETTES = {
    'A': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFB3FF'],  # Soft pink, mint, blue, yellow, lavender
    'B': ['#FFD3B6', '#DCEDC1', '#B5EAD7', '#C7CEEA', '#E2F0CB'],  # Peach, sage, aqua, periwinkle, lime
    'C': ['#F8B195', '#F67280', '#C06C84', '#6C5B7B', '#355C7D'],  # Coral, rose, mauve, purple, navy
    'D': ['#A8E6CF', '#DCEDC1', '#FFD3B6', '#FFAAA5', '#FF8B94'],  # Mint, sage, peach, salmon, pink
    'E': ['#B5EAD7', '#C7CEEA', '#E2F0CB', '#FFDAC1', '#FFB7B2'],  # Aqua, periwinkle, lime, peach, coral
    'F': ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFB3FF'],  # Soft pink, mint, blue, yellow, lavender
    'G': ['#FFD3B6', '#DCEDC1', '#B5EAD7', '#C7CEEA', '#E2F0CB'],  # Peach, sage, aqua, periwinkle, lime
    'H': ['#F8B195', '#F67280', '#C06C84', '#6C5B7B', '#355C7D'],  # Coral, rose, mauve, purple, navy
}

# Base colors for C atoms in each chain
CHAIN_BASE_COLORS = {
    'A': '#FF9AA2',  # Rose (modern pastel)
    'B': '#A2D2FF',  # Sky blue
    'C': '#B5E48C',  # Mint green
    'D': '#FFD6A5',  # Peach
    'E': '#FDFFB6',  # Butter yellow
    'F': '#D0BFFF',  # Lavender purple
    'G': '#FFC6FF',  # Pink lavender
    'H': '#BDE0FE',  # Baby blue
}

def create_selection_cards(selected_chains, selected_hetatm, chain_atoms, atom_colors, atom_sizes, chain_residues):
    """Create selection/rendering cards based on user selections."""
    cards = []
    
    # First, handle water molecules (HOH)
    cards.append("HETATM-----HOH-- 0,9999, 0.5,0.5,0.5, 0.0")
    
    # Handle hydrogen atoms
    cards.append("ATOM  -H-------- 0,9999, 0.5,0.5,0.5, 0.0")
    cards.append("ATOM  H--------- 0,9999, 0.5,0.5,0.5, 0.0")
    
    # Handle all ATOM records for each chain
    for chain in selected_chains:
        if chain_atoms[chain]['ATOM']:
            # Group atoms by their first character (element type)
            atoms_by_element = {}
            for atom in sorted(chain_atoms[chain]['ATOM']):
                # Check if this atom type is selected
                if st.session_state.get(f"chain_{chain}_atom_type_{atom}", False):
                    element = atom[0]  # First character is the element
                    if element not in atoms_by_element:
                        atoms_by_element[element] = []
                    atoms_by_element[element].append(atom)
            
            # Process each element type's atoms
            for element, atoms in atoms_by_element.items():
                for atom in atoms:
                    color = atom_colors.get(f"chain_{chain}_atom_color_{atom}", "#999999")
                    r, g, b = hex_to_rgb(color)
                    size = atom_sizes.get(f"chain_{chain}_atom_size_{atom}", "1.6")
                    cards.append(f"ATOM  -{element}-------{chain} 0,9999, {r},{g},{b}, {size}")
    
    # Handle HETATM records for each chain
    for chain in selected_chains:
        if chain_atoms[chain]['HETATM'] and selected_hetatm:
            # Group HETATM atoms by residue
            hetatm_by_residue = {}
            for atom in sorted(chain_atoms[chain]['HETATM']):
                hetatm_res = atom.split('---')[1] if '---' in atom else ''
                if hetatm_res not in hetatm_by_residue:
                    hetatm_by_residue[hetatm_res] = []
                hetatm_by_residue[hetatm_res].append(atom)
            
            # Create columns for residues
            hetatm_cols = st.columns(min(4, len(hetatm_by_residue)))
            for i, (res_name, atoms) in enumerate(sorted(hetatm_by_residue.items())):
                with hetatm_cols[i % 4]:
                    # Use the first atom as the representative for the residue
                    first_atom = atoms[0]
                    # Create a unique key by combining chain, residue name, and atom
                    unique_key = f"chain_{chain}_hetatm_type_{res_name}_{first_atom}"
                    is_selected = st.checkbox(f"{res_name}", key=unique_key)
                    # Replace nested columns with container and custom CSS
                    st.markdown("""
                        <style>
                        .color-picker-container {
                            display: flex;
                            align-items: center;
                            gap: 10px;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    with st.container():
                        st.markdown('<div class="color-picker-container">', unsafe_allow_html=True)
                        # Use chain-specific color scheme for HETATM as well
                        default_color = get_atom_color(chain, first_atom) if is_selected else '#000000'
                        color = st.color_picker("Color", default_color, key=f"chain_{chain}_hetatm_color_{res_name}_{first_atom}", label_visibility="collapsed")
                        if color:
                            r, g, b = hex_to_rgb(color)
                            st.markdown(f'<div class="rgb-value">{r}, {g}, {b}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add size input in angstroms with default value
                    default_size = ATOM_SIZES.get(first_atom, 1.0) if is_selected else 1.0
                    size = st.number_input(
                        "Size (Å)",
                        min_value=0.1,
                        max_value=10.0,
                        value=default_size,
                        step=0.1,
                        key=f"chain_{chain}_hetatm_size_{res_name}_{first_atom}",
                        disabled=not is_selected
                    )
    return cards

def create_input_file(pdb_file, selected_chains, selected_hetatm, chain_atoms, atom_colors, atom_sizes, center_type, translation, scale, x_rotation, y_rotation, z_rotation, world_params, illustration_params, output_file, chain_residues):
    """Create the input file for ILLUSTRATE program."""
    content = []
    
    # READ command
    content.append("read")
    content.append(pdb_file)
    
    # Add selection/rendering cards
    selection_cards = create_selection_cards(selected_chains, selected_hetatm, chain_atoms, atom_colors, atom_sizes, chain_residues)
    content.extend(selection_cards)
    content.append("END")
    
    # CENTER command
    content.append("center")
    content.append(center_type)
    
    # TRANSLATION command
    content.append("trans")
    content.append(f"{translation[0]},{translation[1]},{translation[2]}")
    
    # SCALE command
    content.append("scale")
    content.append(str(scale))
    
    # ROTATION command
    content.append("xrot")
    content.append(str(x_rotation))
    content.append("yrot")
    content.append(str(y_rotation))
    content.append("zrot")
    content.append(str(z_rotation))
    
    # WORLD command
    content.append("wor")
    world_str = ",".join(map(str, world_params[0:8])) + "\n" + ",".join(map(str, world_params[8:13])) + "\n" + ",".join(map(str, world_params[13:16]))
    content.append(world_str)
    
    # ILLUSTRATE command
    content.append("illustrate")
    for param in illustration_params:
        content.append(param)
    
    # CALCULATE command
    content.append("calculate")
    content.append(output_file)
    
    return "\n".join(content)

def create_atom_descriptor(record_name, atom_desc, res_range_low, res_range_high, color_r, color_g, color_b, radius):
    """Create an atom descriptor string in the format required by ILLUSTRATE."""
    # Format RGB values to 2 significant digits
    color_r = f"{min(max(float(color_r), 0.0), 1.0):.2f}"
    color_g = f"{min(max(float(color_g), 0.0), 1.0):.2f}"
    color_b = f"{min(max(float(color_b), 0.0), 1.0):.2f}"
    return f"{record_name}{atom_desc} {res_range_low},{res_range_high}, {color_r},{color_g},{color_b}, {radius}"

def hex_to_rgb(hex_color):
    """Convert hex color to RGB values (0-1) with 1 significant digit."""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    return tuple(f"{min(max(x, 0.0), 1.0):.1f}" for x in rgb)

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to a temporary location and return the path."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdb') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def get_atom_lines(pdb_content):
    """Extract ATOM and HETATM lines from PDB content."""
    lines = pdb_content.decode('utf-8').split('\n')
    atom_lines = [line for line in lines if line.startswith(('ATOM  ', 'HETATM'))]
    return atom_lines

def get_chain_info(atom_lines):
    """Extract chain information and unique HETATM residue names for each chain."""
    chains = set()
    hetatm_by_chain = defaultdict(set)
    
    for line in atom_lines:
        if len(line) >= 22:  # Ensure line is long enough to contain chain ID
            chain_id = line[21]
            chains.add(chain_id)
            if line.startswith('HETATM'):
                # Extract residue name
                res_name = line[17:20].strip()
                if res_name != 'HOH':  # Skip water molecules
                    hetatm_by_chain[chain_id].add(res_name)
    
    return chains, hetatm_by_chain

def get_unique_atoms(atom_lines, selected_chains, selected_hetatm):
    """Get unique atoms from ATOM and HETATM lines for selected chains and HETATM residues."""
    atom_types = {'ATOM': set(), 'HETATM': set()}
    common_elements = {'C', 'N', 'O', 'S'}  # Common elements to combine
    
    for line in atom_lines:
        if len(line) >= 22:  # Ensure line is long enough to contain chain ID
            chain_id = line[21]
            if chain_id in selected_chains:
                # Extract atom name and element
                atom_name = line[12:16].strip()
                element = atom_name[0]  # First character is usually the element
                res_name = line[17:20].strip()  # Extract residue name
                
                # Skip hydrogen atoms
                if element == 'H':
                    continue
                
                # Skip water molecules
                if line.startswith('HETATM') and res_name == 'HOH':
                    continue
                
                if line.startswith('ATOM  '):
                    if element in common_elements:
                        atom_types['ATOM'].add(element)
                    else:
                        atom_types['ATOM'].add(atom_name)
                elif line.startswith('HETATM'):
                    # Only include HETATM atoms if their residue is selected
                    if res_name in selected_hetatm:
                        # Create a more specific atom identifier including the residue name
                        if element not in common_elements:
                            atom_types['HETATM'].add(f"{atom_name}")
    return atom_types

def get_output_filename(pdb_filename):
    """Generate output filename by replacing .pdb extension with .ppm"""
    if pdb_filename.endswith('.pdb'):
        return pdb_filename[:-4] + '.ppm'
    return pdb_filename + '.ppm'

def get_chain_color(chain, atom_index):
    """Get a color from the chain's pastel palette, cycling through colors."""
    palette = PASTEL_PALETTES.get(chain, PASTEL_PALETTES['A'])  # Default to palette A if chain not found
    return palette[atom_index % len(palette)]

def get_atom_color(chain, atom):
    """Get color for an atom based on the chain's base color and atom type."""
    base_color = CHAIN_BASE_COLORS.get(chain, CHAIN_BASE_COLORS['A'])
    
    # Convert hex to RGB
    r = int(base_color[1:3], 16)
    g = int(base_color[3:5], 16)
    b = int(base_color[5:7], 16)
    
    # Define color variations based on atom type
    if atom == 'C':
        return base_color
    elif atom == 'N':
        # Darker shade
        return f'#{max(0, r-40):02x}{max(0, g-40):02x}{max(0, b-40):02x}'
    elif atom == 'O':
        # Lighter shade
        return f'#{min(255, r+40):02x}{min(255, g+40):02x}{min(255, b+40):02x}'
    elif atom == 'S':
        # More saturated
        return f'#{min(255, int(r*1.2)):02x}{min(255, int(g*1.2)):02x}{min(255, int(b*1.2)):02x}'
    elif atom == 'P':
        # Less saturated
        return f'#{int(r*0.8):02x}{int(g*0.8):02x}{int(b*0.8):02x}'
    else:
        # For other atoms, use a muted version
        return f'#{int(r*0.7):02x}{int(g*0.7):02x}{int(b*0.7):02x}'

def generate_preview(input_file, pdb_file):
    """Generate a preview image using the process.sh script."""
    try:
        # Check if process.sh exists
        if not os.path.exists('process.sh'):
            st.error("process.sh script not found in the current directory")
            return None
            
        # Check if illustrate executable exists
        if not os.path.exists('./illustrate'):
            st.error("illustrate executable not found in the current directory")
            return None
            
        # Make sure process.sh is executable
        try:
            os.chmod('process.sh', 0o755)
        except PermissionError:
            st.error("Permission denied: Cannot make process.sh executable")
            return None
        
        # Run the process script
        try:
            result = subprocess.run(
                ['./process.sh', input_file, pdb_file],
                capture_output=True,
                text=True,
                timeout=30  # Add timeout of 30 seconds
            )
        except subprocess.TimeoutExpired:
            st.error("Preview generation timed out after 30 seconds")
            return None
        except subprocess.CalledProcessError as e:
            st.error(f"Error running process.sh: {e.stderr}")
            return None
        
        if result.returncode == 0:
            # Get the output PNG file path
            output_png = input_file.replace('.inp', '.png')
            if os.path.exists(output_png):
                # Verify the file is a valid image
                try:
                    from PIL import Image
                    Image.open(output_png).verify()
                    return output_png
                except Exception as e:
                    st.error(f"Generated preview file is not a valid image: {str(e)}")
                    # Clean up invalid file
                    try:
                        os.remove(output_png)
                    except:
                        pass
                    return None
            else:
                st.error("Preview image was not generated successfully")
                return None
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            st.error(f"Error generating preview: {error_msg}")
            return None
    except Exception as e:
        st.error(f"Unexpected error during preview generation: {str(e)}")
        return None

def get_chain_residues(atom_lines, selected_chains):
    """Get residues for each selected chain from ATOM and HETATM lines."""
    chain_residues = defaultdict(set)
    
    for line in atom_lines:
        if len(line) >= 22:  # Ensure line is long enough to contain chain ID
            chain_id = line[21]
            if chain_id in selected_chains:
                # Extract residue name and number
                res_name = line[17:20].strip()
                res_num = line[22:26].strip()
                if res_name and res_num:
                    chain_residues[chain_id].add((res_name, res_num))
    st.info(chain_residues)
    # Print the data structure to the console for debugging purposes
    print("[DEBUG] chain_residues:", dict(chain_residues))
    return chain_residues

def main():
    st.title("ILLUSTRATE Input File Generator")
    st.write("Generate input files for the ILLUSTRATE molecular visualization program")

    # Initialize session state variables if they don't exist
    if 'preview_image' not in st.session_state:
        st.session_state.preview_image = None
    if 'pdb_file' not in st.session_state:
        st.session_state.pdb_file = None
    if 'output_file' not in st.session_state:
        st.session_state.output_file = None

    # Initialize variables to prevent UnboundLocalError
    chain_atoms = {}
    chain_residues = {}
    selected_chains = []
    selected_hetatm = set()
    atom_lines = []
    
    # Create two main columns for form and preview
    form_col, preview_col = st.columns([6, 4])
    
    with form_col:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Input & Chains", "Coloring & Size", "View Settings", "Generated Input"])
        
        with tab1:
            st.subheader("1. Input & Chains")
            with st.expander("PDB File Upload", expanded=True):
                # File uploader
                uploaded_file = st.file_uploader("Upload PDB File", type=['pdb'], help="Upload a PDB file to process")
                
                if uploaded_file is not None:
                    # Save the uploaded file
                    pdb_file = save_uploaded_file(uploaded_file)
                    if pdb_file:
                        st.session_state.pdb_file = pdb_file
                        st.session_state.output_file = get_output_filename(uploaded_file.name)
                        st.success(f"Successfully uploaded: {uploaded_file.name}")
                        # Display file info
                        file_size = len(uploaded_file.getvalue()) / 1024  # Size in KB
                        st.write(f"File size: {file_size:.2f} KB")
                
            if uploaded_file is not None:
                with st.expander("ATOM and HETATM Lines Preview", expanded=False):
                    atom_lines = get_atom_lines(uploaded_file.getvalue())
                    if atom_lines:
                        # Create a scrollable text box with all lines
                        st.text_area(
                            "PDB Atom Lines",
                            value='\n'.join(atom_lines),
                            height=200,  # Reduced height for better fit
                            help="Scroll to view all ATOM and HETATM lines"
                        )
                    else:
                        st.warning("No ATOM or HETATM lines found in the file")
            
            with st.expander("Chain Selection", expanded=True):
                atom_descriptors = []
                
                if uploaded_file is not None and atom_lines:
                    chains, hetatm_by_chain = get_chain_info(atom_lines)
                    
                    chain_cols = st.columns(min(4, len(chains)))
                    selected_chains = []
                    for i, chain in enumerate(sorted(chains)):
                        with chain_cols[i % 4]:
                            if st.checkbox(f"Chain {chain}", key=f"chain_{chain}"):
                                selected_chains.append(chain)
                    
                    # Show HETATM selection for selected chains
                    selected_hetatm = set()
                    if selected_chains:
                        for chain in sorted(selected_chains):
                            if hetatm_by_chain[chain]:
                                st.write(f"Chain {chain} HETATM residues:")
                                hetatm_cols = st.columns(min(4, len(hetatm_by_chain[chain])))
                                for i, hetatm in enumerate(sorted(hetatm_by_chain[chain])):
                                    with hetatm_cols[i % 4]:
                                        if st.checkbox(f"{hetatm}", key=f"hetatm_{chain}_{hetatm}"):
                                            selected_hetatm.add(hetatm)
            
            # Output section moved to Input & Chains tab
            with st.expander("Output", expanded=False):
                if uploaded_file is not None:
                    st.session_state.output_file = get_output_filename(uploaded_file.name)
                    st.write(f"Output will be saved as: {st.session_state.output_file}")
                else:
                    st.info("Upload a PDB file to see the output filename")
                
                if st.button("Generate Input File"):
                    if not uploaded_file or not st.session_state.pdb_file:
                        st.warning("Please upload a PDB file first")
                        return
                        
                    chain_atoms = {}
                    chain_residues = get_chain_residues(atom_lines, selected_chains)
                    for chain in selected_chains:
                        chain_atoms[chain] = get_unique_atoms(atom_lines, [chain], selected_hetatm)
                    
                    input_content = create_input_file(
                        st.session_state.pdb_file, selected_chains, selected_hetatm, chain_atoms,
                        st.session_state, st.session_state,  # For atom_colors and atom_sizes
                        center_type, translation, scale, x_rotation, y_rotation, z_rotation,
                        world_params, illustration_params, st.session_state.output_file, chain_residues
                    )
                    
                    # Save the input file
                    try:
                        input_file_path = st.session_state.output_file.replace('.ppm', '.inp')
                        with open(input_file_path, "w") as f:
                            f.write(input_content)
                        # st.info(f"Input file saved as: {os.path.abspath(input_file_path)}")
                    except IOError as e:
                        st.error(f"Failed to save input file: {str(e)}")
                    return
        
        with tab2:
            st.subheader("2. Coloring and Size Scheme")
            if uploaded_file is not None and atom_lines and selected_chains:
                # Get unique atoms for each selected chain
                chain_atoms = {}
                for chain in selected_chains:
                    chain_atoms[chain] = get_unique_atoms(atom_lines, [chain], selected_hetatm)
                
                # Create tabs for each chain
                chain_tabs = st.tabs([f"Chain {chain}" for chain in sorted(selected_chains)])
                
                # For each chain tab
                for chain_idx, chain in enumerate(sorted(selected_chains)):
                    with chain_tabs[chain_idx]:
                        with st.expander(f"ATOM Types", expanded=False):
                            if chain_atoms[chain]['ATOM']:
                                atom_cols = st.columns(min(4, len(chain_atoms[chain]['ATOM'])))
                                for i, atom in enumerate(sorted(chain_atoms[chain]['ATOM'])):
                                    with atom_cols[i % 4]:
                                        # Set default to True for all ATOM types
                                        is_selected = st.checkbox(f"{atom}", value=True, key=f"chain_{chain}_atom_type_{atom}")
                                        # Replace nested columns with container and custom CSS
                                        st.markdown("""
                                            <style>
                                            .color-picker-container {
                                                display: flex;
                                                align-items: center;
                                                gap: 10px;
                                            }
                                            </style>
                                        """, unsafe_allow_html=True)
                                        
                                        with st.container():
                                            st.markdown('<div class="color-picker-container">', unsafe_allow_html=True)
                                            # Use chain-specific color scheme based on C atom color
                                            default_color = get_atom_color(chain, atom) if is_selected else '#000000'
                                            color = st.color_picker("Color", default_color, key=f"chain_{chain}_atom_color_{atom}", label_visibility="collapsed")
                                            if color:
                                                r, g, b = hex_to_rgb(color)
                                                st.markdown(f'<div class="rgb-value">{r}, {g}, {b}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        # Add size input in angstroms with default value
                                        default_size = ATOM_SIZES.get(atom, 1.0) if is_selected else 1.0
                                        size = st.number_input(
                                            "Size (Å)",
                                            min_value=0.1,
                                            max_value=10.0,
                                            value=default_size,
                                            step=0.1,
                                            key=f"chain_{chain}_atom_size_{atom}",
                                            disabled=not is_selected
                                        )
                        
                        if chain_atoms[chain]['HETATM'] and selected_hetatm:
                            with st.expander(f"HETATM Types", expanded=False):
                                # Group HETATM atoms by residue
                                hetatm_by_residue = {}
                                for atom in sorted(chain_atoms[chain]['HETATM']):
                                    hetatm_res = atom.split('---')[1] if '---' in atom else ''
                                    if hetatm_res not in hetatm_by_residue:
                                        hetatm_by_residue[hetatm_res] = []
                                    hetatm_by_residue[hetatm_res].append(atom)
                                
                                # Create columns for residues
                                hetatm_cols = st.columns(min(4, len(hetatm_by_residue)))
                                for i, (res_name, atoms) in enumerate(sorted(hetatm_by_residue.items())):
                                    with hetatm_cols[i % 4]:
                                        # Use the first atom as the representative for the residue
                                        first_atom = atoms[0]
                                        # Create a unique key by combining chain, residue name, and atom
                                        unique_key = f"chain_{chain}_hetatm_type_{res_name}_{first_atom}"
                                        is_selected = st.checkbox(f"{res_name}", key=unique_key)
                                        # Replace nested columns with container and custom CSS
                                        st.markdown("""
                                            <style>
                                            .color-picker-container {
                                                display: flex;
                                                align-items: center;
                                                gap: 10px;
                                            }
                                            </style>
                                        """, unsafe_allow_html=True)
                                        
                                        with st.container():
                                            st.markdown('<div class="color-picker-container">', unsafe_allow_html=True)
                                            # Use chain-specific color scheme for HETATM as well
                                            default_color = get_atom_color(chain, first_atom) if is_selected else '#000000'
                                            color = st.color_picker("Color", default_color, key=f"chain_{chain}_hetatm_color_{res_name}_{first_atom}", label_visibility="collapsed")
                                            if color:
                                                r, g, b = hex_to_rgb(color)
                                                st.markdown(f'<div class="rgb-value">{r}, {g}, {b}</div>', unsafe_allow_html=True)
                                            st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        # Add size input in angstroms with default value
                                        default_size = ATOM_SIZES.get(first_atom, 1.0) if is_selected else 1.0
                                        size = st.number_input(
                                            "Size (Å)",
                                            min_value=0.1,
                                            max_value=10.0,
                                            value=default_size,
                                            step=0.1,
                                            key=f"chain_{chain}_hetatm_size_{res_name}_{first_atom}",
                                            disabled=not is_selected
                                        )
        
        with tab3:
            st.subheader("3. View Settings")
            
            # Create expandable sections for different parameter groups
            with st.expander("Centering & Translation", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    center_type = st.selectbox("Center Type", ["auto", "cen"])
                with col2:
                    st.write("Translation")
                    x_trans = st.number_input("X Translation", value=0.0)
                    y_trans = st.number_input("Y Translation", value=0.0)
                    z_trans = st.number_input("Z Translation", value=0.0)
                translation = (x_trans, y_trans, z_trans)
            
            with st.expander("Scale & Rotation", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    scale = st.number_input("Scale Factor", value=12.0, step=1.0)
                with col2:
                    x_rotation = st.number_input("X Rotation (degrees)", value=0.0, step=1.0)
                    y_rotation = st.number_input("Y Rotation (degrees)", value=0.0, step=1.0)
                    z_rotation = st.number_input("Z Rotation (degrees)", value=90.0, step=1.0)
            
            with st.expander("World Parameters", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Background Color (RGB)")
                    bg_r = st.number_input("Background R", value=1.0)
                    bg_g = st.number_input("Background G", value=1.0)
                    bg_b = st.number_input("Background B", value=1.0)
                    
                    st.write("Fog Color (RGB)")
                    fog_r = st.number_input("Fog R", value=1.0)
                    fog_g = st.number_input("Fog G", value=1.0)
                    fog_b = st.number_input("Fog B", value=1.0)
                
                with col2:
                    st.write("Fog Settings")
                    fog_front = st.number_input("Front Fog Opacity", value=1.0)
                    fog_back = st.number_input("Back Fog Opacity", value=1.0)
                    
                    st.write("Image Size")
                    size_x = st.number_input("Size X", value=-30)
                    size_y = st.number_input("Size Y", value=-30)
            
            with st.expander("Shadow Parameters", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    shadow_flag = st.number_input("Shadow Flag", value=1)
                with col2:
                    shadow_contribution = st.number_input("Shadow Contribution", value=0.0023)
                with col3:
                    shadow_angle = st.number_input("Shadow Angle", value=2.0)
                
                col1, col2 = st.columns(2)
                with col1:
                    shadow_z = st.number_input("Shadow Z", value=1.0)
                with col2:
                    shadow_max = st.number_input("Shadow Max", value=0.2)
            
            with st.expander("Illustration Parameters", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Contour Outlines")
                    contour_low = st.number_input("Contour Low", value=3.0)
                    contour_high = st.number_input("Contour High", value=10.0)
                    kernel = st.number_input("Kernel", value=4)
                    diff_min = st.number_input("Diff Min", value=0.0)
                    diff_max = st.number_input("Diff Max", value=5.0)
                
                with col2:
                    st.write("Subunit & Residue Outlines")
                    subunit_low = st.number_input("Subunit Low", value=3.0)
                    subunit_high = st.number_input("Subunit High", value=10.0)
                    residue_low = st.number_input("Residue Low", value=3.0)
                    residue_high = st.number_input("Residue High", value=8.0)
                    residue_diff = st.number_input("Residue Diff", value=6000.0)
            
            world_params = [bg_r, bg_g, bg_b, fog_r, fog_g, fog_b, fog_front, fog_back,
                          shadow_flag, shadow_contribution, shadow_angle, shadow_z, shadow_max,
                          size_x, size_y]
            
            illustration_params = [
                f"{contour_low},{contour_high},{kernel},{diff_min},{diff_max}",
                f"{subunit_low},{subunit_high}",
                f"{residue_low},{residue_high},{residue_diff}"
            ]
        
    # Add the new tab content for showing generated input
    with tab4:
        st.subheader("Generated Input File")
        if uploaded_file is not None and st.session_state.pdb_file and st.session_state.output_file:
            try:
                # Generate the input file content
                if not chain_atoms and atom_lines and selected_chains:
                    chain_residues = get_chain_residues(atom_lines, selected_chains)
                    for chain in selected_chains:
                        chain_atoms[chain] = get_unique_atoms(atom_lines, [chain], selected_hetatm)

                input_content = create_input_file(
                    st.session_state.pdb_file, selected_chains, selected_hetatm, chain_atoms,
                    st.session_state, st.session_state,  # For atom_colors and atom_sizes
                    center_type, translation, scale, x_rotation, y_rotation, z_rotation,
                    world_params, illustration_params, st.session_state.output_file, chain_residues
                )
                
                # Display the generated input file in a text area
                st.text_area(
                    "ILLUSTRATE Input File",
                    value=input_content,
                    height=400,
                    help="This is the generated input file that will be used by ILLUSTRATE",
                    key="generated_input_area"
                )
                
                # Create two columns for the buttons
                col1, col2 = st.columns([1, 1])
                
                # Add download button in the left column
                with col1:
                    st.download_button(
                        label="Download Input File",
                        data=input_content,
                        file_name=st.session_state.output_file,
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Error generating input file: {str(e)}")
        else:
            st.info("Upload a PDB file to see the generated input file")

    with preview_col:
        # Initialize session state for preview image if not exists
        if 'preview_image' not in st.session_state:
            st.session_state.preview_image = None
        
        # Add custom CSS for centering
        st.markdown("""
            <style>
            div[data-testid="stImage"] {
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #f0f2f6;
                border-radius: 5px;
                padding: 20px;
                margin: 100px 100px;
            }
            div[data-testid="stImage"] img {
                width: 400px !important;
                max-width: 100% !important;
                height: auto !important;
            }
            div[data-testid="stImageCaption"] {
                width: 400px !important;
                max-width: 100% !important;
                text-align: center !important;
            }
            div[data-testid="stButton"] {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 20px 0;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Show either the generated preview or a placeholder
        if st.session_state.preview_image and os.path.exists(st.session_state.preview_image):
            st.image(st.session_state.preview_image, 
                    caption="Molecular Structure Preview",
                    width=600)
        elif not st.session_state.preview_image:
            st.info("Upload a PDB file and click Preview to generate the molecular structure visualization")
        
        # Add Preview button below the image
        st.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
        if st.button("Preview", type="primary", key="preview_button_preview_panel"):
            try:
                # Save the input file
                input_file_path = st.session_state.output_file.replace('.ppm', '.inp')
                with open(input_file_path, "w") as f:
                    f.write(input_content)
                # st.info(f"Input file saved as: {os.path.abspath(input_file_path)}")
                
                # Generate preview
                with st.spinner("Generating preview..."):
                    preview_image = generate_preview(input_file_path, st.session_state.pdb_file)
                    if preview_image:
                        st.session_state.preview_image = preview_image
                        # st.success("Preview generated successfully!")
                        # st.info(f"Output PNG path: {os.path.abspath(preview_image)}")
                    else:
                        st.session_state.preview_image = None
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.session_state.preview_image = None
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 