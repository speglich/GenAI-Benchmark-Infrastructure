#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot multi-abordagens (OCI + várias variantes VLLM) em um mesmo gráfico.

Novo formato: dentro de results/, cada subpasta representa uma abordagem/variante.
Dentro de cada subpasta, há vários arquivos JSON, cada um para uma combinação de cenário/concurrency.

Cada JSON tem:
- "aggregated_metrics": dict com estatísticas agregadas
- "individual_request_metrics": lista (não utilizada na agregação principal)

Gera:
- PNG por métrica (uma linha por subpasta/cenário)
- CSV consolidado
- Multiplot com 8 métricas principais

Autor: Copilot adaptado para múltiplos cenários e métricas agregadas
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

try:
    import seaborn as sns
    HAS_SNS = True
except Exception:
    HAS_SNS = False

PREFERRED_STATS = ["p95", "mean", "value"]

PRETTY_TITLES = {
    "ttft": "Time To First Token (TTFT) [s]",
    "e2e_latency": "End-to-end latency (s)",
    "output_throughput": "Output throughput (tokens/s)",
    "output_inference_speed": "Output inference speed (tokens/s)",
    "num_completed_requests": "Completed requests",
    "error_rate": "Error rate",
    "num_input_tokens": "Input tokens",
    "num_output_tokens": "Output tokens",
    "total_tokens": "Total tokens",
    "input_throughput": "Input throughput (tokens/s)",
    "output_latency": "Output Latency (s)",
    "mean_output_throughput_tokens_per_s": "Mean Output Throughput (tokens/s)",
    "mean_input_throughput_tokens_per_s": "Mean Input Throughput (tokens/s)",
    "mean_total_tokens_throughput_tokens_per_s": "Mean Total Tokens Throughput (tokens/s)",
    "mean_total_chars_per_hour": "Mean Total Chars per Hour",
    "requests_per_second": "Requests per Second",
    "tpot": "Time Per Output Token (TPOT) [s]",
    # Adicione mais se quiser
}

AGG_METRICS_TO_INCLUDE = [
    "mean_output_throughput_tokens_per_s",
    "mean_input_throughput_tokens_per_s",
    "mean_total_tokens_throughput_tokens_per_s",
    "mean_total_chars_per_hour",
    "requests_per_second",
]

# Métricas para o multiplot
MULTIPLOT_METRICS = [
    "e2e_latency",
    "ttft",
    "tpot",
    "requests_per_second",
    "output_latency",
    "output_inference_speed",
    "mean_total_tokens_throughput_tokens_per_s",
    "mean_output_throughput_tokens_per_s"
]

def to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        if not s or s.startswith("{") or s.startswith("["):
            return None
        try:
            return float(s)
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        return float(value)
    return None

def extract_concurrency(json_data, filename: str) -> Optional[int]:
    # Preferencialmente pega do JSON
    if "aggregated_metrics" in json_data and "num_concurrency" in json_data["aggregated_metrics"]:
        return json_data["aggregated_metrics"]["num_concurrency"]
    m = re.search(r"_concurrency_(\d+)_", filename)
    if m:
        return int(m.group(1))
    return None

def discover_json_files(platform_dir: Path) -> List[Path]:
    return sorted([f for f in platform_dir.glob("*.json") if f.is_file()])

def load_platform_rows(platform_dir: Path, platform_label: str) -> List[Dict]:
    rows: List[Dict] = []
    for json_file in discover_json_files(platform_dir):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        agg = data.get("aggregated_metrics", {})
        stats = agg.get("stats", {})
        scenario = agg.get("scenario")
        concurrency = agg.get("num_concurrency") if "num_concurrency" in agg else extract_concurrency(data, json_file.name)
        # 1. Adiciona stats como antes
        for metric, stat_dict in stats.items():
            for stat, value in stat_dict.items():
                val = to_float(value)
                if val is None:
                    continue
                rows.append({
                    "platform_label": platform_label,
                    "scenario": scenario,
                    "metric_base": metric,
                    "stat": stat.lower(),
                    "concurrency": concurrency,
                    "value": val,
                })
        # 2. Adiciona métricas agregadas solicitadas
        for metric in AGG_METRICS_TO_INCLUDE:
            val = to_float(agg.get(metric))
            if val is not None:
                rows.append({
                    "platform_label": platform_label,
                    "scenario": scenario,
                    "metric_base": metric,
                    "stat": "mean",
                    "concurrency": concurrency,
                    "value": val,
                })
        # 3. Adiciona outras agregadas simples (ex: error_rate)
        for metric in ["error_rate", "num_completed_requests"]:
            val = to_float(agg.get(metric))
            if val is not None:
                rows.append({
                    "platform_label": platform_label,
                    "scenario": scenario,
                    "metric_base": metric,
                    "stat": "value",
                    "concurrency": concurrency,
                    "value": val,
                })
    return rows

def build_dataframe(root: Path, scenarios_filter: Optional[List[str]] = None, concurrencies_filter: Optional[List[int]] = None) -> pd.DataFrame:
    rows: List[Dict] = []
    for platform_dir in sorted(root.iterdir()):
        if not platform_dir.is_dir():
            continue
        platform_label = platform_dir.name
        platform_rows = load_platform_rows(platform_dir, platform_label)
        if scenarios_filter:
            platform_rows = [row for row in platform_rows if row["scenario"] in scenarios_filter]
        if concurrencies_filter:
            platform_rows = [row for row in platform_rows if row["concurrency"] in concurrencies_filter]
        rows.extend(platform_rows)
    if not rows:
        raise SystemExit("Nenhum dado numérico encontrado no novo formato.")
    df = pd.DataFrame(rows)
    return df.sort_values(["metric_base", "stat", "platform_label", "scenario", "concurrency"]).reset_index(drop=True)

def choose_stat_for_metric(df_metric: pd.DataFrame, only_p95: bool = False) -> str:
    available = set(df_metric["stat"].unique())
    if only_p95:
        if "p95" in available:
            return "p95"
        return sorted(available)[0]
    for pref in PREFERRED_STATS:
        if pref in available:
            return pref
    return sorted(available)[0]

def pretty_title(metric_base: str) -> str:
    return PRETTY_TITLES.get(metric_base, metric_base)

def human_fmt(x: float) -> str:
    if x == 0:
        return "0"
    absx = abs(x)
    if absx >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if absx >= 1_000:
        return f"{x/1_000:.2f}k"
    if absx >= 100:
        return f"{x:.0f}"
    if absx >= 10:
        return f"{x:.1f}"
    return f"{x:.2f}"

def setup_style():
    if HAS_SNS:
        sns.set_theme(context="talk", style="whitegrid", palette="colorblind")
    else:
        plt.style.use("seaborn-v0_8-whitegrid")

def build_labels(df: pd.DataFrame, legend_format: str) -> pd.DataFrame:
    df = df.copy()
    def make_label(row):
        return legend_format.format(
            platform=row["platform_label"],
            scenario=row["scenario"],
        )
    df["label"] = df.apply(make_label, axis=1)
    return df

def plot_multiplot(
    df: pd.DataFrame,
    out_dir: Path,
    logx: bool,
    show: bool,
    experiment_name: Optional[str] = None,
):
    """Cria um multiplot com 8 métricas principais em uma grade 2x4"""
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_style()

    labels = sorted(df["label"].unique())
    base_colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", ["#1f77b4", "#ff7f0e"])
    if HAS_SNS and len(labels) > len(base_colors):
        extra = sns.color_palette("tab20", n_colors=max(len(labels), 20))
        palette = extra
    else:
        repeats = (len(labels) // len(base_colors)) + 1
        palette = (base_colors * repeats)[: len(labels)]
    color_map = dict(zip(labels, palette))

    # Filtra apenas as métricas do multiplot
    df_multiplot = df[df["metric_base"].isin(MULTIPLOT_METRICS)]
    available_metrics = [m for m in MULTIPLOT_METRICS if m in df_multiplot["metric_base"].unique()]

    if not available_metrics:
        print("[AVISO] Nenhuma métrica do multiplot encontrada nos dados.")
        return

    # Cria figura com subplots 2x4
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    axes = axes.flatten()

    # Título geral da figura
    if experiment_name:
        fig.suptitle(f"{experiment_name} - Performance Metrics Overview", fontsize=16, y=0.98)
    else:
        fig.suptitle("Performance Metrics Overview", fontsize=16, y=0.98)

    for i, metric in enumerate(available_metrics):
        if i >= len(axes):
            break

        ax = axes[i]
        dsub = df_multiplot[df_multiplot["metric_base"] == metric]

        if dsub.empty:
            ax.set_visible(False)
            continue

        chosen_stat = dsub["stat"].iloc[0]

        # Plot das linhas para cada label
        handles = []
        for label in labels:
            dline = dsub[dsub["label"] == label].sort_values("concurrency")
            if dline.empty:
                continue
            h = ax.plot(
                dline["concurrency"],
                dline["value"],
                label=label,
                color=color_map[label],
                linewidth=2,
                marker="o",
                markersize=4,
                alpha=0.9,
            )[0]
            handles.append(h)

            # Anotação do último valor
            if len(dline) > 0:
                last = dline.iloc[-1]
                ax.annotate(
                    human_fmt(last["value"]),
                    xy=(last["concurrency"], last["value"]),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=8,
                    color=color_map[label],
                    weight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color_map[label], alpha=0.7),
                )

        stat_label = "P95" if chosen_stat == "p95" else ("Mean" if chosen_stat == "mean" else chosen_stat)
        metric_title = pretty_title(metric)

        ax.set_title(f"{metric_title}", fontsize=12, pad=8)
        ax.set_xlabel("Concurrency", fontsize=10)
        ax.set_ylabel(metric_title, fontsize=10)

        if logx:
            ax.set_xscale("log", base=2)
            xticks = sorted(dsub["concurrency"].unique())
            ax.set_xticks(xticks)
            ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        else:
            ax.set_xticks(sorted(dsub["concurrency"].unique()))

        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=9)

    # Remove subplots não utilizados
    for i in range(len(available_metrics), len(axes)):
        axes[i].set_visible(False)

    # Legenda global
    if labels:
        # Pega os handles da primeira subplot que tem dados
        legend_handles = []
        for i, metric in enumerate(available_metrics):
            dsub = df_multiplot[df_multiplot["metric_base"] == metric]
            if not dsub.empty:
                for label in labels:
                    dline = dsub[dsub["label"] == label].sort_values("concurrency")
                    if not dline.empty:
                        h = plt.Line2D([0], [0], color=color_map[label], linewidth=2, label=label)
                        legend_handles.append(h)
                break

        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_handles = []
        for h in legend_handles:
            if h.get_label() not in seen:
                seen.add(h.get_label())
                unique_handles.append(h)

        fig.legend(
            unique_handles,
            [h.get_label() for h in unique_handles],
            loc='center',
            bbox_to_anchor=(0.5, 0.02),
            ncol=min(len(unique_handles), 4),
            fontsize=10,
            frameon=True,
            framealpha=0.9
        )

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.12)

    # Salva o multiplot
    multiplot_path = out_dir / "multiplot_overview.png"
    fig.savefig(multiplot_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Multiplot: {multiplot_path}")

    plt.close(fig)
    if show:
        plt.show()

def plot_metrics(
    df: pd.DataFrame,
    out_dir: Path,
    logx: bool,
    show: bool,
    experiment_name: Optional[str] = None,
):
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_style()
    labels = sorted(df["label"].unique())
    base_colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", ["#1f77b4", "#ff7f0e"])
    if HAS_SNS and len(labels) > len(base_colors):
        extra = sns.color_palette("tab20", n_colors=max(len(labels), 20))
        palette = extra
    else:
        repeats = (len(labels) // len(base_colors)) + 1
        palette = (base_colors * repeats)[: len(labels)]
    color_map = dict(zip(labels, palette))
    metrics = df["metric_base"].unique().tolist()
    for metric in metrics:
        dsub = df[df["metric_base"] == metric]
        if dsub.empty:
            continue
        chosen_stat = dsub["stat"].iloc[0]
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        handles = []
        for label in labels:
            dline = dsub[dsub["label"] == label].sort_values("concurrency")
            if dline.empty:
                continue
            h = ax.plot(
                dline["concurrency"],
                dline["value"],
                label=label,
                color=color_map[label],
                linewidth=2.3,
                marker="o",
                markersize=6.5,
                alpha=0.95,
            )[0]
            handles.append(h)
            last = dline.iloc[-1]
            ax.annotate(
                human_fmt(last["value"]),
                xy=(last["concurrency"], last["value"]),
                xytext=(5, 6),
                textcoords="offset points",
                fontsize=10,
                color=color_map[label],
                weight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color_map[label], alpha=0.85),
            )
        stat_label = "P95" if chosen_stat == "p95" else ("Mean" if chosen_stat == "mean" else chosen_stat)
        metric_title = pretty_title(metric)

        # Monta o título com o nome do experimento, se fornecido
        if experiment_name:
            title = f"{experiment_name} - {metric_title} — {stat_label}"
        else:
            title = f"{metric_title} — {stat_label}"

        ax.set_title(title, pad=10)
        ax.set_xlabel("Concurrency")
        ax.set_ylabel(metric_title)
        if logx:
            ax.set_xscale("log", base=2)
            xticks = sorted(dsub["concurrency"].unique())
            ax.set_xticks(xticks)
            ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
        else:
            ax.set_xticks(sorted(dsub["concurrency"].unique()))
        ax.grid(True, linestyle="--", linewidth=0.55, alpha=0.35)
        leg = ax.legend(
            handles=handles,
            loc="upper left",
            frameon=True,
            framealpha=0.92,
            ncol=1 if len(labels) < 10 else 2,
            fontsize=9,
        )
        for lh in leg.legend_handles:
            lh.set_linewidth(2.8)
        fig.tight_layout()
        safe = re.sub(r"[^a-zA-Z0-9_\-]+", "_", metric)
        png_path = out_dir / f"{safe}_{stat_label.lower()}.png"
        fig.savefig(png_path, dpi=220)
        print(f"[OK] Figura: {png_path}")
        plt.close(fig)
        if show:
            plt.show()

def sanitize_experiment_name(name: str) -> str:
    """Sanitiza o nome do experimento para uso como nome de diretório"""
    return re.sub(r"[^a-zA-Z0-9_\-\s]+", "_", name).strip()

def main():
    parser = argparse.ArgumentParser(description="Plota múltiplas abordagens usando múltiplos cenários (novo formato + métricas agregadas).")
    parser.add_argument("--root", type=Path, default=Path("results"), help="Raiz contendo pastas de variantes.")
    parser.add_argument("--scenarios", nargs="*", help="Filtrar cenários (conforme chave 'scenario' do JSON).")
    parser.add_argument("--concurrencies", type=str, help="Filtrar concorrências específicas (ex: '1,2,4,8,16,32'). Se não especificado, usa todas.")
    parser.add_argument("--legend-format", default="{platform}-{scenario}", help="Template do rótulo (placeholders: {platform},{scenario})")
    parser.add_argument("--out-dir", type=Path, default=Path("figures_multi"), help="Diretório de saída (será sobrescrito se --experiment for usado).")
    parser.add_argument("--experiment", type=str, help="Nome do experimento (ex: 'Llama 3.3 70B', 'Scout', 'Maverick')")
    parser.add_argument("--logx", action="store_true", help="Escala log2 no eixo X.")
    parser.add_argument("--show", action="store_true", help="Mostrar interativamente.")
    parser.add_argument("--only-p95", action="store_true", help="Força usar somente p95 se existir (fallback).")
    parser.add_argument("--skip-individual", action="store_true", help="Pula gráficos individuais, gera apenas o multiplot.")
    args = parser.parse_args()

    # Parse concurrencies filter
    concurrencies_filter = None
    if args.concurrencies:
        try:
            concurrencies_filter = [int(x.strip()) for x in args.concurrencies.split(',')]
            print(f"[INFO] Filtrando concorrências: {concurrencies_filter}")
        except ValueError:
            raise SystemExit("Erro: --concurrencies deve ser uma lista de números separados por vírgula (ex: '1,2,4,8,16,32')")

    # Determina o diretório de saída baseado no experimento
    if args.experiment:
        sanitized_name = sanitize_experiment_name(args.experiment)
        output_dir = Path("figures") / sanitized_name
    else:
        output_dir = args.out_dir

    raw_df = build_dataframe(args.root, scenarios_filter=args.scenarios, concurrencies_filter=concurrencies_filter)
    # Escolhe por métrica a estatística (globalmente).
    chosen_parts = []
    for metric in raw_df["metric_base"].unique():
        dm = raw_df[raw_df["metric_base"] == metric]
        stat = choose_stat_for_metric(dm, only_p95=args.only_p95)
        chosen_parts.append(dm[dm["stat"] == stat])
    df_pref = pd.concat(chosen_parts, ignore_index=True)
    # Constrói labels
    df_pref = build_labels(df_pref, args.legend_format)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "metrics_selected_multi.csv"
    df_pref.sort_values(["metric_base", "platform_label", "scenario", "concurrency"]).to_csv(csv_path, index=False)
    print(f"[OK] CSV consolidado: {csv_path}")

    # Gera o multiplot
    plot_multiplot(df_pref, output_dir, logx=args.logx, show=args.show, experiment_name=args.experiment)

    # Gera gráficos individuais (a menos que seja explicitamente desabilitado)
    if not args.skip_individual:
        plot_metrics(df_pref, output_dir, logx=args.logx, show=args.show, experiment_name=args.experiment)

if __name__ == "__main__":
    main()