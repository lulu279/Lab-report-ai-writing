"""Create editable SVG plus PNG; figures are always derived from actual input rows."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_figures(df, curves, config, folder: Path) -> list[str]:
    folder.mkdir(parents=True, exist_ok=True)
    output = []
    for sample in config.samples:
        sub = df[df.sample_id == sample.sample_id]
        fig, ax = plt.subplots(figsize=(7.2, 4.0))
        for segment, group in sub.groupby("segment", sort=False):
            ax.plot(group.temperature_c, group.heat_flow_mw, label=segment, lw=1.3)
        ax.set_xlabel("Temperature / °C")
        ax.set_ylabel("Heat flow / mW (as recorded)")
        ax.set_title(f"{sample.sample_id} | DSC segments")
        ax.legend(fontsize=8)
        ax.grid(alpha=.2)
        if config.dataset_type == "synthetic":
            ax.text(.5,.45,"SYNTHETIC TEST DATA",transform=ax.transAxes,alpha=.2,
                    fontsize=16,rotation=15,ha="center")
        fig.tight_layout()
        for suffix in ("png","svg"):
            name = f"{sample.sample_id}_overview.{suffix}"
            fig.savefig(folder / name, dpi=300, bbox_inches="tight")
            output.append(str(Path("figures")/name))
        plt.close(fig)
    for win in config.windows:
        content = curves[win.event_id]
        frame, baseline = content["frame"], content["baseline"]
        fig, ax = plt.subplots(figsize=(6.4,3.6))
        ax.plot(frame.temperature_c, frame.heat_flow_mw, label="Measured heat flow",lw=1.5)
        ax.plot(frame.temperature_c, baseline, ls="--", label=("Linear endpoint baseline" if win.baseline_method=="linear_endpoint_mean" else "Constant endpoint baseline"),lw=1.0)
        ax.fill_between(frame.temperature_c,frame.heat_flow_mw,baseline,alpha=.16)
        ax.set_xlabel("Temperature / °C")
        ax.set_ylabel("Heat flow / mW (as recorded)")
        ax.set_title(f"{win.event_id} | {win.phase}")
        ax.legend(fontsize=8)
        ax.grid(alpha=.2)
        if config.dataset_type == "synthetic":
            ax.text(.5,.46,"SYNTHETIC",transform=ax.transAxes,fontsize=20,
                    alpha=.18,rotation=15,ha="center")
        fig.tight_layout()
        for suffix in ("png","svg"):
            name = f"{win.event_id}.{suffix}"
            fig.savefig(folder / name,dpi=300,bbox_inches="tight")
            output.append(str(Path("figures")/name))
        plt.close(fig)
    return output
