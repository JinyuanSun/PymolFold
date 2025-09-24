import re, os, json, requests
import streamlit as st
from rdkit import Chem

EXAMPLES = [
    {
        "title": "A transcription factor and DNA complex",
        "description": (
            "DNA Chain A:\n"
            "TGGGTCACGTGTTCC\n\n"
            "DNA Chain B:\n"
            "AGGAACACGTGACCC\n\n"
            "PROTEIN Chain C:\n"
            "MGREEPLNHVEAERQRREKLNQRFRYALRAVVPVNVSKMDKASLLGDATAYINELKSKVVKTESEKLQIKNQLEEVKLELAGRLEHHHHHH\n\n"
            "PROTEIN Chain D:\n"
            "MGREEPLNHVEAERQRREKLNQRFRYALRAVVPVNVSKMDKASLLGDATAYINELKSKVVKTESEKLQIKNQLEEVKLELAGRLEHHHHHH"
        ),
        "entities": [
            {
                "type": "DNA",
                "chain_id": "A",
                "sequence": "TGGGTCACGTGTTCC",
            },
            {
                "type": "DNA",
                "chain_id": "B",
                "sequence": "AGGAACACGTGACCC",
            },
            {
                "type": "Protein",
                "chain_id": "C",
                "sequence": (
                    "MGREEPLNHVEAERQRREKLNQRFRYALRAVVPVNVSKMDKASLLGDATAYINELKSKVVKTESEKLQIKNQLEEVKLELAGRLEHHHHHH"
                ),
            },
            {
                "type": "Protein",
                "chain_id": "D",
                "sequence": (
                    "MGREEPLNHVEAERQRREKLNQRFRYALRAVVPVNVSKMDKASLLGDATAYINELKSKVVKTESEKLQIKNQLEEVKLELAGRLEHHHHHH"
                ),
            },
        ],
    },
    {
        "title": "A protein-ligand complex (ATP)",
        "description": (
            "PROTEIN Chain A:\n"
            "MTEYKKLVVVGAGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQ\n\n"
            "LIGAND(CCD) Chain B:\n"
            "ATP"
        ),
        "entities": [
            {
                "type": "Protein",
                "chain_id": "A",
                "sequence": (
                    "MTEYKKLVVVGAGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQEEYSAMRDQ"
                ),
            },
            {
                "type": "Ligand (CCD)",
                "chain_id": "B",
                "ccd_string": "ATP",
            },
        ],
    },
]

EXIST_CCD = json.load(
    open(os.path.join(os.path.dirname(__file__), "ccd_keys.json"), "rb")
)

# --- Session State Initialization ---
if "entities" not in st.session_state:
    st.session_state.entities = [
        {"type": "Protein", "chain_id": "A", "sequence": "", "modifications": []}
    ]
# New session keys for submission lifecycle
if "run_errors" not in st.session_state:
    st.session_state.run_errors = []
if "final_data" not in st.session_state:
    st.session_state.final_data = None
if "run_submitted" not in st.session_state:
    st.session_state.run_submitted = False
if "run_success" not in st.session_state:
    st.session_state.run_success = False
if "run_server_msg" not in st.session_state:
    st.session_state.run_server_msg = ""
if "running" not in st.session_state:
    st.session_state.running = False


def is_valid_dna(seq: str) -> bool:
    return bool(re.fullmatch(r"[ACGT]+", seq.upper()))


def is_valid_rna(seq: str) -> bool:
    return bool(re.fullmatch(r"[ACGU]+", seq.upper()))


def is_valid_protein(seq: str) -> bool:
    # 20 standard amino acids
    return bool(re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWY]+", seq.upper()))


def check_CCD(s: str) -> bool:
    return s in EXIST_CCD


def check_SMILES(s: str) -> bool:
    try:
        if Chem.MolFromSmiles(s) is None:
            return False
    except:
        return False
    return True


# --- Callback Functions ---
def get_next_chain_id():
    existing_ids = {
        entity.get("chain_id", "") for entity in st.session_state.get("entities", [])
    }
    for i in range(26):
        next_id = chr(ord("A") + i)
        if next_id not in existing_ids:
            return next_id
    return "X"


def add_new_entity():
    entity_type = st.session_state.entity_select
    new_entity = {"type": entity_type, "chain_id": get_next_chain_id()}
    if entity_type in ["Protein", "RNA", "DNA"]:
        new_entity["sequence"] = ""
        new_entity["modifications"] = []
    elif entity_type == "Ligand (CCD)":
        new_entity["ccd_string"] = ""
    elif entity_type == "Ligand (SMILES)":
        new_entity["smiles_string"] = ""
    st.session_state.entities.append(new_entity)


def clear_all_entities():
    st.session_state.entities = [
        {"type": "Protein", "chain_id": "A", "sequence": "", "modifications": []}
    ]
    # It's good practice to clear other potential state keys as well
    if "show_examples_dialog" in st.session_state:
        del st.session_state["show_examples_dialog"]


def remove_entity(index):
    if len(st.session_state.entities) > index:
        st.session_state.entities.pop(index)


def add_modification(entity_index):
    entity = st.session_state.entities[entity_index]
    if len(entity.get("modifications", [])) < 3:
        entity.setdefault("modifications", []).append({"residue_index": 1, "ccd": ""})


def remove_modification(entity_index, mod_index):
    if (
        len(st.session_state.entities[entity_index].get("modifications", []))
        > mod_index
    ):
        st.session_state.entities[entity_index]["modifications"].pop(mod_index)


def load_example(example_index):
    new_entities = EXAMPLES[example_index]["entities"]
    for entity in new_entities:
        if entity["type"] in ["Protein", "RNA", "DNA"]:
            # Ensure modifications list exists when loading examples
            entity["modifications"] = entity.get("modifications", [])
    st.session_state.entities = new_entities


# --- UI Rendering Functions ---
def render_modifications(entity, entity_index):
    if st.button(
        "+ Modification",
        help="Add up to 3 modifications to the sequence.",
        key=f"add_mod_{entity_index}",
        on_click=add_modification,
        args=(entity_index,),
    ):
        pass

    for mod_index, mod in enumerate(entity.get("modifications", [])):
        mod_cols = st.columns([5, 5, 1])
        with mod_cols[0]:
            st.number_input(
                "Residue Index *",
                min_value=1,
                step=1,
                value=mod.get("residue_index"),
                key=f"mod_idx_{entity_index}_{mod_index}",
                placeholder="eg 1 position",
                help="Enter the residue index number for the modification.",
            )
        with mod_cols[1]:
            st.text_input(
                "CCD *",
                value=mod.get("ccd", ""),
                key=f"mod_ccd_{entity_index}_{mod_index}",
                placeholder="eg ATP",
                help="Input a CCD for the modification.",
            )
        with mod_cols[2]:
            st.button(
                "🗑️",
                key=f"del_mod_{entity_index}_{mod_index}",
                on_click=remove_modification,
                args=(entity_index, mod_index),
                help="Delete modification",
            )


def render_protein_card(entity, index):
    with st.container(border=True):
        cols = st.columns([10, 1])
        cols[0].subheader(f"PROTEIN CHAIN_ID: {entity['chain_id']}")
        cols[1].button(
            "🗑️",
            key=f"del_prot_{index}",
            on_click=remove_entity,
            args=(index,),
            help="Delete this entity",
        )

        st.text_area(
            "Protein Sequence *",
            value=entity.get("sequence", ""),
            key=f"seq_prot_{index}",
            height=100,
            placeholder="Enter Sequence here",
        )

        cols = st.columns([2, 2, 6])
        # cols[0].button("+ Add MSA", key=f"msa_{index}")
        cols[0].toggle(
            "Cyclic",
            key=f"cyc_prot_{index}",
            help="Whether the polymer forms a cyclic structure",
        )

        st.write("Add Modifications (3 maximum)")
        render_modifications(entity, index)


def render_rna_card(entity, index):
    with st.container(border=True):
        cols = st.columns([10, 1])
        cols[0].subheader(f"RNA CHAIN_ID: {entity['chain_id']}")
        cols[1].button(
            "🗑️",
            key=f"del_rna_{index}",
            on_click=remove_entity,
            args=(index,),
            help="Delete this entity",
        )
        st.text_input(
            "RNA Sequence *",
            value=entity.get("sequence", ""),
            key=f"seq_rna_{index}",
            placeholder="Enter Sequence here",
        )
        st.toggle("Cyclic", key=f"cyc_rna_{index}")
        st.write("Add Modifications (3 maximum)")
        render_modifications(entity, index)


def render_dna_card(entity, index):
    with st.container(border=True):
        cols = st.columns([10, 1])
        cols[0].subheader(f"DNA CHAIN_ID: {entity['chain_id']}")
        cols[1].button(
            "🗑️",
            key=f"del_dna_{index}",
            on_click=remove_entity,
            args=(index,),
            help="Delete this entity",
        )
        st.text_input(
            "DNA Sequence *",
            value=entity.get("sequence", ""),
            key=f"seq_dna_{index}",
            placeholder="Enter Sequence here",
        )
        st.toggle("Cyclic", key=f"cyc_dna_{index}")
        st.write("Add Modifications (3 maximum)")
        render_modifications(entity, index)


def render_ligand_ccd_card(entity, index):
    with st.container(border=True):
        cols = st.columns([10, 1])
        cols[0].subheader(f"LIGAND(CCD) CHAIN_ID: {entity['chain_id']}")
        cols[1].button(
            "🗑️",
            key=f"del_ccd_{index}",
            on_click=remove_entity,
            args=(index,),
            help="Delete this entity",
        )
        # st.info("Note: Only CCD Ligands have the potential to bond.", icon="ℹ️")
        st.text_input(
            "CCD String *",
            value=entity.get("ccd_string", ""),
            key=f"ccd_{index}",
            placeholder="eg = ATP (adenosine triphosphate)",
        )


def render_ligand_smiles_card(entity, index):
    with st.container(border=True):
        cols = st.columns([10, 1])
        cols[0].subheader(f"LIGAND(SMILES) CHAIN_ID: {entity['chain_id']}")
        cols[1].button(
            "🗑️",
            key=f"del_smi_{index}",
            on_click=remove_entity,
            args=(index,),
            help="Delete this entity",
        )
        # st.info("Note: Only CCD Ligands have the potential to bond.", icon="ℹ️")
        st.text_input(
            "SMILES String *",
            value=entity.get("smiles_string", ""),
            key=f"smi_{index}",
            placeholder="eg = C1CCCCC2CCCCC12 (Decalin)",
        )


def gather_submission_data():
    """
    Collects all user inputs from st.session_state by iterating through the entities
    and constructing the keys for each widget.
    """
    submission = {}
    entities = []
    # Add the optional entity name if it exists
    if st.session_state.get("entity_name"):
        submission["name"] = st.session_state.entity_name

    if st.session_state.get("diffusion_samples"):
        submission["diffusion_samples"] = st.session_state.diffusion_samples

    for i, entity in enumerate(st.session_state.entities):
        entity_data = {"type": entity["type"], "chain_id": entity["chain_id"]}

        if entity["type"] == "Protein":
            entity_data["sequence"] = st.session_state.get(f"seq_prot_{i}", "")
            entity_data["cyclic"] = st.session_state.get(f"cyc_prot_{i}", False)
            mods = []
            for mod_i in range(len(entity.get("modifications", []))):
                mod_data = {
                    "residue_index": st.session_state.get(f"mod_idx_{i}_{mod_i}"),
                    "ccd": st.session_state.get(f"mod_ccd_{i}_{mod_i}", ""),
                }
                mods.append(mod_data)
            entity_data["modifications"] = mods

        elif entity["type"] == "RNA":
            entity_data["sequence"] = st.session_state.get(f"seq_rna_{i}", "")
            entity_data["cyclic"] = st.session_state.get(f"cyc_rna_{i}", False)
            mods = []
            for mod_i in range(len(entity.get("modifications", []))):
                mod_data = {
                    "residue_index": st.session_state.get(f"mod_idx_{i}_{mod_i}"),
                    "ccd": st.session_state.get(f"mod_ccd_{i}_{mod_i}", ""),
                }
                mods.append(mod_data)
            entity_data["modifications"] = mods

        elif entity["type"] == "DNA":
            entity_data["sequence"] = st.session_state.get(f"seq_dna_{i}", "")
            entity_data["cyclic"] = st.session_state.get(f"cyc_dna_{i}", False)
            mods = []
            for mod_i in range(len(entity.get("modifications", []))):
                mod_data = {
                    "residue_index": st.session_state.get(f"mod_idx_{i}_{mod_i}"),
                    "ccd": st.session_state.get(f"mod_ccd_{i}_{mod_i}", ""),
                }
                mods.append(mod_data)
            entity_data["modifications"] = mods

        elif entity["type"] == "Ligand (CCD)":
            entity_data["ccd_string"] = st.session_state.get(f"ccd_{i}", "")

        elif entity["type"] == "Ligand (SMILES)":
            entity_data["smiles_string"] = st.session_state.get(f"smi_{i}", "")

        entities.append(entity_data)
    submission["entities"] = entities
    return submission


# New unified submission callback using session state
def run_submission():
    st.session_state.running = True
    st.session_state.run_errors = []
    st.session_state.run_success = False
    st.session_state.run_server_msg = ""
    final_data = gather_submission_data()
    errors = []
    for ent in final_data["entities"]:
        t = ent["type"]
        if t == "DNA" and not is_valid_dna(ent.get("sequence", "")):
            errors.append(
                f"DNA Chain {ent['chain_id']} contains invalid characters (must be A/C/G/T)."
            )
        elif t == "RNA" and not is_valid_rna(ent.get("sequence", "")):
            errors.append(
                f"RNA Chain {ent['chain_id']} contains invalid characters (must be A/C/G/U)."
            )
        elif t == "Protein" and not is_valid_protein(ent.get("sequence", "")):
            errors.append(
                f"Protein Chain {ent['chain_id']} contains invalid characters (20 amino acids only)."
            )
        elif t == "Ligand (CCD)" and not check_CCD(ent.get("ccd_string", "")):
            errors.append(
                f"Ligand (CCD) Chain {ent['chain_id']} is invalid CCD string."
            )
        elif t == "Ligand (SMILES)" and not check_SMILES(ent.get("smiles_string", "")):
            errors.append(
                f"Ligand (SMILES) Chain {ent['chain_id']} is not a valid SMILES."
            )
    st.session_state.final_data = final_data
    st.session_state.run_errors = errors
    st.session_state.run_submitted = True
    if errors:
        st.session_state.running = False
        return
    # Attach affinity settings if applicable
    has_sequence = any(
        e["type"] in ["Protein", "RNA", "DNA"] for e in final_data["entities"]
    )
    has_ligand = any("Ligand" in e["type"] for e in final_data["entities"])
    if has_sequence and has_ligand:
        affinity_settings = {
            "calculate_affinity": st.session_state.get(
                "calculate_affinity_checkbox", False
            ),
            "selected_ligand": st.session_state.get("affinity_ligand_select"),
        }
        final_data["binding_affinity_settings"] = affinity_settings
    try:
        resp = requests.post(
            "http://127.0.0.1:5002/run_boltz2",
            json={"sub_data": final_data},
            timeout=400,
        )
        if resp.status_code == 200:
            st.session_state.run_success = True
            st.session_state.run_server_msg = (
                "Submission sent to PyMOL plugin successfully!"
            )
        else:
            st.session_state.run_server_msg = f"Plugin server error: {resp.text}"
    except Exception as e:
        st.session_state.run_server_msg = f"Could not contact local plugin server: {e}"
    finally:
        st.session_state.running = False


# --- Main Application UI ---
st.set_page_config(page_title="Boltz2-Interface", layout="wide")

title_cols = st.columns([8, 2])
with title_cols[0]:
    st.title("Add entities to fold.")
with title_cols[1]:
    if st.button("View Examples", use_container_width=True):
        st.session_state.show_examples_dialog = True

st.text_input(
    "Entity Name (Optional)", key="entity_name", placeholder="e.g., Test Complex"
)
st.number_input(
    "How many structure samples you want to get?",
    min_value=1,
    max_value=5,
    value=1,
    step=1,
    key="diffusion_samples",
)
# --- Example Dialog Logic ---
if st.session_state.get("show_examples_dialog", False):
    st.dialog("Select an Example")
    formatted_options = [
        f"**{ex['title']}**\n```\n{ex['description']}\n```" for ex in EXAMPLES
    ]
    selected_example_str = st.radio(
        "Select an example from the list:", formatted_options, key="example_choice"
    )

    if st.button("Done", use_container_width=True, type="primary"):
        selected_index = formatted_options.index(selected_example_str)
        load_example(selected_index)
        st.session_state.show_examples_dialog = False
        st.rerun()

# --- Top Control Bar ---
top_cols = st.columns([2, 1, 1, 6])
with top_cols[0]:
    st.selectbox(
        "Select entity to add",
        ["Protein", "RNA", "DNA", "Ligand (SMILES)", "Ligand (CCD)"],
        key="entity_select",
        label_visibility="collapsed",
    )
with top_cols[1]:
    st.button("+ New", on_click=add_new_entity, use_container_width=True)
# with top_cols[2]:
#     st.button("🗑️ Clear All", on_click=clear_all_entities, use_container_width=True)

st.markdown("---")

# --- Dynamic Rendering of all Entity Cards ---
for i, entity in enumerate(st.session_state.entities):
    entity_type = entity["type"]
    if entity_type == "Protein":
        render_protein_card(entity, i)
    elif entity_type == "RNA":
        render_rna_card(entity, i)
    elif entity_type == "DNA":
        render_dna_card(entity, i)
    elif entity_type == "Ligand (CCD)":
        render_ligand_ccd_card(entity, i)
    elif entity_type == "Ligand (SMILES)":
        render_ligand_smiles_card(entity, i)

# --- Conditional Rendering of the Affinity Module ---
entity_types_present = {e["type"] for e in st.session_state.entities}
has_sequence = any(t in entity_types_present for t in ["Protein", "RNA", "DNA"])
has_ligand = any(t in entity_types_present for t in ["Ligand (SMILES)", "Ligand (CCD)"])

if has_sequence and has_ligand:
    st.markdown("---")
    st.subheader("Binding Affinity")
    ligand_options = [
        f"{e['type']} CHAIN_ID: {e['chain_id']}"
        for e in st.session_state.entities
        if "Ligand" in e["type"]
    ]
    st.selectbox(
        "Select ligand to calculate affinity",
        ligand_options,
        key="affinity_ligand_select",
    )
    st.checkbox("Calculate Affinity", value=True, key="calculate_affinity_checkbox")
else:
    st.markdown("---")
    st.info(
        "Add at least one sequence entity (Protein/DNA/RNA) and one ligand entity (Ligand) to enable binding affinity prediction."
    )


footer_cols = st.columns([8, 1, 1])
with footer_cols[1]:
    st.button("Reset", use_container_width=True, on_click=clear_all_entities)

with footer_cols[2]:
    # Simplified Run button using callback; validation + submission handled in run_submission
    st.button("Run", type="primary", use_container_width=True, on_click=run_submission)

# Unified status / results area (moved outside footer columns)
if st.session_state.get("running"):
    st.info("Running simulation...")
elif st.session_state.get("run_submitted"):
    if st.session_state.run_errors:
        st.error("❌ Validation failed. Please fix the following issues:")
        for e in st.session_state.run_errors:
            st.markdown(f"- {e}")
    else:
        if st.session_state.run_success:
            st.success(st.session_state.run_server_msg or "Submission completed.")
        else:
            if st.session_state.run_server_msg:
                st.warning(st.session_state.run_server_msg)

# Optional: allow user to inspect submission JSON
if st.session_state.get("final_data") and st.checkbox("Show submission JSON"):
    st.json(st.session_state.final_data)

st.caption(
    """
This page is a non-commercial reproduction of [Boltz2 on NVIDIA Build](https://build.nvidia.com/mit/boltz2). 
"""
)
