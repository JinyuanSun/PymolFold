"""Utility functions for structure prediction and analysis"""

import re
import json
from pathlib import Path
import subprocess
import sys
from typing import Union, Dict, Any
from pymol import cmd as pymol_cmd


def pip_install(pkg, index_url=None):
    cmd = [sys.executable, "-m", "pip", "install", pkg]
    if index_url:
        cmd.extend(["-i", index_url])
    print(f"[PfPlugin] Installing {pkg}...")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        for line in process.stdout:
            print(line.strip())
        process.wait()
        if process.returncode == 0:
            print(f"[PfPlugin] {pkg} installed successfully.")
        else:
            print(f"[PfPlugin] Failed to install {pkg}")
    except Exception as e:
        print(f"[PfPlugin] Failed to install {pkg}: {e}")


def cal_plddt(pdb_string: str) -> float:
    """Calculate average pLDDT score from PDB B-factors

    Args:
        pdb_string: PDB format structure string

    Returns:
        Average pLDDT score (0-100 scale)
    """
    lines = pdb_string.split("\n")
    plddts = []

    for line in lines:
        if " CA " in line:
            try:
                plddt = float(line[60:66])
                plddts.append(plddt)
            except (ValueError, IndexError):
                continue

    if not plddts:
        return 0.0

    # Convert 0-1 scale to 0-100 if needed
    if max(plddts) <= 1.0:
        plddts = [plddt * 100 for plddt in plddts]

    return sum(plddts) / len(plddts)


def color_plddt(selection="all"):
    """
    AUTHOR
    Jinyuan Sun

    DESCRIPTION
    Colors Predicted Structures by pLDDT

    USAGE
    color_plddt sele

    PARAMETERS

    sele (string)
    The name of the selection/object to color by pLDDT. Default: all
    """
    # Alphafold color scheme for plddt
    pymol_cmd.set_color("high_lddt_c", [0, 0.325490196078431, 0.843137254901961])
    pymol_cmd.set_color(
        "normal_lddt_c", [0.341176470588235, 0.792156862745098, 0.976470588235294]
    )
    pymol_cmd.set_color("medium_lddt_c", [1, 0.858823529411765, 0.070588235294118])
    pymol_cmd.set_color("low_lddt_c", [1, 0.494117647058824, 0.270588235294118])

    # test the scale of predicted_lddt (0~1 or 0~100 ) as b-factors
    pymol_cmd.select("test_b_scale", f"b>1 and ({selection})")
    b_scale = pymol_cmd.count_atoms("test_b_scale")

    if b_scale > 0:
        pymol_cmd.select("high_lddt", f"({selection}) and (b >90 or b =90)")
        pymol_cmd.select(
            "normal_lddt", f"({selection}) and ((b <90 and b >70) or (b =70))"
        )
        pymol_cmd.select(
            "medium_lddt", f"({selection}) and ((b <70 and b >50) or (b=50))"
        )
        pymol_cmd.select("low_lddt", f"({selection}) and ((b <50 and b >0) or (b=0))")
    else:
        pymol_cmd.select("high_lddt", f"({selection}) and (b >.90 or b =.90)")
        pymol_cmd.select(
            "normal_lddt", f"({selection}) and ((b <.90 and b >.70) or (b =.70))"
        )
        pymol_cmd.select(
            "medium_lddt", f"({selection}) and ((b <.70 and b >.50) or (b=.50))"
        )
        pymol_cmd.select("low_lddt", f"({selection}) and ((b <.50 and b > 0) or (b=0))")

    pymol_cmd.delete("test_b_scale")

    # set color based on plddt values
    pymol_cmd.color("high_lddt_c", "high_lddt")
    pymol_cmd.color("normal_lddt_c", "normal_lddt")
    pymol_cmd.color("medium_lddt_c", "medium_lddt")
    pymol_cmd.color("low_lddt_c", "low_lddt")

    # set background color
    pymol_cmd.bg_color("white")


def clean_sequence(sequence: str) -> str:
    """Clean amino acid sequence string

    Args:
        sequence: Raw sequence string

    Returns:
        Cleaned sequence with only valid amino acid letters
    """
    # Replace "/" with ":" and convert to uppercase
    sequence = re.sub("[^A-Z:]", "", sequence.replace("/", ":").upper())
    # Clean up colons
    sequence = re.sub(":+", ":", sequence)
    sequence = re.sub("^[:]+", "", sequence)
    sequence = re.sub("[:]+$", "", sequence)
    return sequence


def safe_filename(name: str) -> str:
    """Convert string to safe filename

    Args:
        name: Original filename string

    Returns:
        Safe filename with invalid characters removed/replaced
    """
    name = name.strip()
    # Remove/replace invalid characters
    name = re.sub(r"[\/\\\0]", "_", name)
    # Collapse multiple spaces/underscores
    name = re.sub(r"\s+", "_", name)
    return name or "model"


def save_json_output(
    data: Dict[str, Any], output_file: Union[str, Path], indent: int = 4
) -> Path:
    """Save prediction results to JSON file

    Args:
        data: Prediction results dictionary
        output_file: Output JSON file path
        indent: JSON indentation level

    Returns:
        Path to saved file
    """
    output_path = Path(output_file)
    output_path.write_text(json.dumps(data, indent=indent), encoding="utf-8")
    return output_path


def visualize_pxmeter_metrics(data: dict, output_dir: str = "metrics_output"):
    """
    Parses a metrics JSON, handles missing keys gracefully, and outputs
    a comprehensive summary CSV and several specific visualization plots (bar chart and heatmaps).

    Args:
        data (dict): The input JSON data as a Python dictionary.
        output_dir (str): The directory to save the output files.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    from pathlib import Path

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    entry_id = data.get("entry_id", "unknown_entry")
    print(f"Visualizing Entry ID: {entry_id}")

    # --- 1. Enhanced Data Preparation ---
    metrics_list = []
    complex_metrics = data.get("complex", {})
    metrics_list.append(
        {
            "Level": "Complex",
            "Chain/Interface": "Overall",
            "Metric": "lDDT",
            "Value": complex_metrics.get("lddt"),
        }
    )
    metrics_list.append(
        {
            "Level": "Complex",
            "Chain/Interface": "Overall",
            "Metric": "Clashes",
            "Value": complex_metrics.get("clashes"),
        }
    )

    chain_metrics = data.get("chain", {})
    for chain_id, chain_data in chain_metrics.items():
        metrics_list.append(
            {
                "Level": "Chain",
                "Chain/Interface": f"Chain {chain_id}",
                "Metric": "lDDT",
                "Value": chain_data.get("lddt"),
            }
        )

    interface_metrics = data.get("interface", {})
    for interface_id, interface_data in interface_metrics.items():
        metrics_list.append(
            {
                "Level": "Interface",
                "Chain/Interface": interface_id,
                "Metric": "lDDT",
                "Value": interface_data.get("lddt"),
            }
        )
        if "dockq" in interface_data:
            metrics_list.append(
                {
                    "Level": "Interface",
                    "Chain/Interface": interface_id,
                    "Metric": "DockQ",
                    "Value": interface_data.get("dockq"),
                }
            )

        dockq_info = interface_data.get("dockq_info", {})
        for key, value in dockq_info.items():
            if key in ["F1", "iRMSD", "LRMSD", "fnat"]:
                metrics_list.append(
                    {
                        "Level": "Interface",
                        "Chain/Interface": interface_id,
                        "Metric": key,
                        "Value": value,
                    }
                )

    # --- 2. Create and Save Comprehensive CSV ---
    df = pd.DataFrame(metrics_list)
    df.dropna(subset=["Value"], inplace=True)
    csv_path = Path(output_dir) / f"{entry_id}_summary_metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"✓ Comprehensive summary metrics saved to: {csv_path}")

    # --- 3. Set publication-style formatting ---
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.5)

    # Plot 1: Combined Complex and Chain lDDT Scores (bar chart, publication style)
    lddt_df = df[
        (df["Metric"] == "lDDT") & (df["Level"].isin(["Complex", "Chain"]))
    ].copy()
    if not lddt_df.empty:
        lddt_df["sort_key"] = lddt_df["Chain/Interface"].apply(
            lambda x: f"0_{x}" if x == "Overall" else f"1_{x}"
        )
        lddt_df.sort_values("sort_key", inplace=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        bar_palette = {"Overall": "#8dd3c7"}
        for chain in lddt_df["Chain/Interface"]:
            if chain not in bar_palette:
                bar_palette[chain] = "#80b1d3"
        sns.barplot(
            x="Chain/Interface",
            y="Value",
            data=lddt_df,
            palette=bar_palette,
            hue="Chain/Interface",
            dodge=False,
            ax=ax,
        )
        ax.set_title(
            f"Overall Complex and Per-Chain lDDT Scores for {entry_id}",
            fontsize=20,
            pad=20,
        )
        ax.set_ylabel("lDDT Score", fontsize=16, labelpad=15)
        ax.set_xlabel("Entity", fontsize=16, labelpad=15)
        ax.set_ylim(0, 1.05)
        ax.tick_params(axis="both", which="major", labelsize=14)
        ax.grid(which="major", linestyle="--", linewidth="0.7")
        for spine in ax.spines.values():
            spine.set_edgecolor("black")
            spine.set_linewidth(1.2)
        for p in ax.patches:
            ax.annotate(
                f"{p.get_height(): .3f}",
                (p.get_x() + p.get_width() / 2.0, p.get_height()),
                ha="center",
                va="center",
                fontsize=13,
                color="black",
                xytext=(0, 5),
                textcoords="offset points",
            )
        plt.legend([], [], frameon=False)
        plt.tight_layout()
        plot_path = Path(output_dir) / f"{entry_id}_combined_lddt.png"
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"✓ Combined lDDT plot saved to: {plot_path}")

    # --- Plot 2: Interface Scores as N x N Heatmaps (3x2 grid, publication style) ---
    interface_df = df[df["Level"] == "Interface"]
    unique_chains = sorted(list(data.get("chain", {}).keys()))

    if not unique_chains:
        print("No chain information found, skipping heatmap generation.")
        return

    metrics_to_plot = ["lDDT", "DockQ", "F1", "iRMSD", "LRMSD", "fnat"]
    heatmap_matrices = []
    titles = []

    for metric in metrics_to_plot:
        metric_df = interface_df[interface_df["Metric"] == metric]
        if not metric_df.empty:
            heatmap_matrix = pd.DataFrame(
                index=unique_chains, columns=unique_chains, dtype=float
            )
            for _, row in metric_df.iterrows():
                chains = row["Chain/Interface"].split(",")
                if len(chains) == 2:
                    chain1, chain2 = chains
                    value = row["Value"]
                    heatmap_matrix.loc[chain1, chain2] = value
                    heatmap_matrix.loc[chain2, chain1] = value
            heatmap_matrices.append(heatmap_matrix)
            titles.append(f"Interface {metric}")

    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    axes = axes.flatten()

    # Publication-style color, font, border
    for i, (matrix, title) in enumerate(zip(heatmap_matrices, titles)):
        metric = metrics_to_plot[i]
        mask = matrix.isnull()
        sns.heatmap(
            matrix,
            annot=True,
            fmt=".3f",
            cmap="viridis",
            linewidths=0.7,
            mask=mask,
            cbar_kws={"label": f"{metric} Score"},
            ax=axes[i],
            annot_kws={"fontsize": 13},
        )
        axes[i].set_title(title, fontsize=18, pad=15)
        axes[i].set_xlabel("Chain ID", fontsize=15, labelpad=10)
        axes[i].set_ylabel("Chain ID", fontsize=15, labelpad=10)
        axes[i].tick_params(axis="both", which="major", labelsize=13)
        for spine in axes[i].spines.values():
            spine.set_edgecolor("black")
            spine.set_linewidth(1.2)

    for j in range(len(heatmap_matrices), 6):
        fig.delaxes(axes[j])

    fig.suptitle(
        f"Interface Metrics Heatmaps for {entry_id}", fontsize=22, fontweight="bold"
    )
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plot_path = Path(output_dir) / f"{entry_id}_interface_metrics_grid.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ All interface metric heatmaps saved to: {plot_path}")
