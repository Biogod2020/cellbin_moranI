import matplotlib.pyplot as plt
import seaborn as sns
import scanpy as sc
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler
from .palettes import cell_type_colors, general_type_colors, brain_region_colors, age_group_colors

def plot_normalized_umap(
    slide: dict,
    num_rows: int = 1,
    num_cols: int = 7,
    cell_type: str = "Micro",
    color: str = "min_center_dist",
    palette: dict = cell_type_colors,
    **umap_kwargs
) -> plt.Figure:
    """
    Plots a grid of UMAP projections with normalized values for each AnnData object in 'slide'.

    Args:
        slide: Dictionary where keys are identifiers and values are AnnData objects.
        num_rows: Number of rows in the subplot grid.
        num_cols: Number of columns in the subplot grid.
        cell_type: The cell type to filter on for plotting. If None, plot all cells.
        color: The column name in `adata.obs` to normalize and plot.
        palette: Optional dictionary specifying the color palette to use if 'color' is categorical.
        **umap_kwargs: Arbitrary keyword arguments to pass to the `sc.pl.umap` function.

    Returns:
        plt.Figure: The matplotlib figure object.
    """
    def normalize(values):
        min_val = values.min()
        max_val = values.max()
        return (values - min_val) / (max_val - min_val)

    # Determine the number of subplots needed
    # num_plots = len(slide)
    # Create a grid of subplots
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(num_cols * 4, num_rows * 4), gridspec_kw={'width_ratios': [1] * num_cols})
    axes = axes.flatten()  # Flatten the array to easily iterate through it

    # Rearrange the slide items to start with the second key and put the first key last
    slide_items = list(slide.items())
    slide_items = slide_items[1:] + slide_items[:1]

    # Plot each adata in the appropriate subplot
    for i, (key, adata) in enumerate(slide_items):
        tmp = adata.copy()
        if i >= len(axes):  # Prevent indexing errors if there are more slides than subplots
            break
        if (i < len(axes) - 1) or isinstance(tmp.obs[color][0], (int, float, complex)):
            leg_stat = None
        else:
            leg_stat = "right margin"

        if cell_type:
            mask = tmp.obs["celltype"] == cell_type
        else:
            mask = slice(None)  # Select all cells if cell_type is None

        if color == "min_center_dist":
            tmp.obs.loc[mask, f"{color}_normalized"] = normalize(tmp.obs.loc[mask, color])
            plot_color = f"{color}_normalized"
        else:
            plot_color = color

        sc.pl.umap(tmp[mask], color=plot_color, vmin=0, vmax=1 if color == "min_center_dist" else None, 
                   ax=axes[i], show=False, colorbar_loc=None, legend_loc=leg_stat, palette=palette, **umap_kwargs)
        axes[i].set_title(key.split(sep="_")[0])
        for pos in ['top', 'bottom', 'left']:
            axes[i].spines[pos].set_visible(False)
        axes[i].set_xlabel("")
        axes[i].set_ylabel("")

    # Add an axis for the color bar on the right border if color is numerical and default
    if isinstance(tmp.obs[color][0], (int, float, complex)):
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # [left, bottom, width, height]
        norm = plt.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.set_label(f'{color}_normalized')

    plt.tight_layout(rect=[0, 0, 0.9, 1])  # Adjust layout to make space for the color bar
    return fig


def save_figure_to_pdf(fig: plt.Figure, filename: str, dpi: int = 300) -> None:
    """
    Saves the given figure object to a PDF file.

    Args:
        fig: The matplotlib figure object to save.
        filename: The name of the output PDF file.
        dpi: The resolution of the output PDF file.
    """
    with PdfPages(filename) as pdf:
        fig.savefig(pdf, format='pdf', dpi=dpi)


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler
import numpy as np

def plot_kde_normalized_distance(
    pfcdf: pd.DataFrame,
    cell_type: str = "Micro",
    dist_col: str = "min_center_dist",
    fine_col: str = "fine",
    palette: dict = cell_type_colors,
    save_path: str = None,
    fig_size: tuple = (8, 4),
    dpi: int = 350,
    scaling_method: str = "standard",  # Parameter to choose the scaling method
    ax: plt.Axes = None,
    **kde_kwargs
) -> plt.Axes:
    """
    Plots a KDE of normalized and log-transformed distances for a specific cell type in the DataFrame.

    Args:
        pfcdf: DataFrame containing the data.
        cell_type: The cell type to filter on for plotting.
        dist_col: The column name in `pfcdf` to normalize and plot.
        fine_col: The column name representing finer categorization to plot separately.
        palette: Optional dictionary specifying the color palette to use for each `fine` value.
        save_path: Optional path where the plot should be saved. If None, the plot will not be saved.
        fig_size: Size of the figure.
        dpi: Dots per inch for saving the figure.
        scaling_method: Method to use for scaling ('standard', 'minmax', 'maxabs').
        ax: Optional matplotlib axis object to draw on. If None, a new figure and axis will be created.
        **kde_kwargs: Arbitrary keyword arguments to pass to the `sns.kdeplot` function.

    Returns:
        plt.Axes: The matplotlib axis object used for plotting.
    """
    def scale_values(values, method):
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        elif method == "maxabs":
            scaler = MaxAbsScaler()
        else:
            raise ValueError("Unsupported scaling method. Choose from 'standard', 'minmax', or 'maxabs'.")
        return scaler.fit_transform(values.reshape(-1, 1)).flatten()
    
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=fig_size)
    else:
        fig = ax.figure
        
    mask = (pfcdf["celltype"] == cell_type) & (pfcdf[dist_col] > 0)
    filtered_data = pfcdf[mask]
    filtered_data = filtered_data.copy()
    filtered_data["fine"] = filtered_data[fine_col].astype(str)

    # Scale the distance values
    filtered_data["dist_scaled"] = scale_values(filtered_data[dist_col].values, scaling_method)
    filtered_data["Normalized and -log10 transformed distance"] = -np.log10(filtered_data["dist_scaled"] + 1e-3)
    plot_color = "Normalized and -log10 transformed distance"

    # Iterate over each unique 'fine' value to plot the KDEs separately
    for fine_value in filtered_data["fine"].unique():
        sns.kdeplot(
            data=filtered_data[filtered_data["fine"] == fine_value],
            x=plot_color,
            label=fine_value,
            ax=ax,
            color=palette[fine_value] if palette else None,
            fill=True,
            alpha=0.3,
            **kde_kwargs
        )

    ax.grid(visible=False)
    ax.legend(title="Cell's Subtypes")  # Add a legend to differentiate KDEs

    # Save the figure only if a save path is provided
    if save_path:
        plt.savefig(save_path, dpi=dpi)

    plt.show()
    
    return ax

def plot_genes_in_spatial(
    adata_input,
    sample_ids: list = None,
    genes: list = [
        "Rbfox3", "Map2", "Gap43", "Syn1", "Nefl",
        "Vim", "Gfap", "Eno2", "Tubb3", "Camk2a"
    ],
    cut_off: float = 99.5,
    fig_size_per_gene: tuple = (4, 4),
    gene_col: str = "gene",
    sample_col: str = "sample",
    embedding_basis: str = "spatial",
    size: int = 6,
    save_path: str = None,
    dpi: int = 350,
    **kwargs
) -> plt.Figure:
    """
    Plots spatial embeddings for a list of neuronal soma genes across multiple samples.

    Args:
        adata_input: Either an AnnData object or a dictionary of AnnData objects.
        sample_ids: List of sample identifiers to plot. If None, will be derived from adata_input.
        genes: List of genes to plot. Defaults to a predefined list of neuronal soma genes.
        fig_size_per_gene: Size of the figure for each gene subplot.
        gene_col: Column name for genes in the AnnData object.
        sample_col: Column name for samples in the AnnData object.
        embedding_basis: Basis for spatial embedding in the AnnData object.
        size: Size of the points in the plot.
        save_path: Optional path where the plot should be saved. If None, the plot will not be saved.
        dpi: Dots per inch for saving the figure.
        **kwargs: Additional keyword arguments to pass to `sc.pl.embedding`.

    Returns:
        plt.Figure: The matplotlib figure object used for plotting.
    """

    # Determine sample IDs if not provided
    if sample_ids is None:
        if isinstance(adata_input, dict):
            sample_ids = list(adata_input.keys())
        else:
            sample_ids = adata_input.obs[sample_col].unique().tolist()

    # Calculate top 0.5% value for each gene
    if cut_off:
        top_5_percent_values = {}
        for gene in genes:
            all_values = []
            if isinstance(adata_input, dict):
                for adata in adata_input.values():
                    if gene in adata.var_names:
                        all_values.extend(adata[:, gene].X.flatten())
            else:
                if gene in adata_input.var_names:
                    all_values.extend(adata_input[:, gene].X.flatten())
    
            if all_values:
                top_5_percent_values[gene] = np.percentile(all_values, cut_off)

    n_genes = len(genes)
    n_samples = len(sample_ids)

    fig_size = (fig_size_per_gene[0] * n_samples, fig_size_per_gene[1] * n_genes)
    fig, axs = plt.subplots(n_genes, n_samples, figsize=fig_size)

    for i, gene in enumerate(genes):
        if cut_off:
            vmax = top_5_percent_values.get(gene, None)
        else:
            vmax = 5
        for j, sample_id in enumerate(sample_ids):
            ax = axs[i, j] if n_genes > 1 and n_samples > 1 else (axs[j] if n_genes == 1 else axs[i])
            try:
                if isinstance(adata_input, dict):
                    adata_sample = adata_input[sample_id]
                else:
                    adata_sample = adata_input[adata_input.obs[sample_col] == sample_id]

                sc.pl.embedding(
                    adata_sample,
                    basis=embedding_basis,
                    ax=ax,
                    color=gene,
                    size=size,
                    show=False,
                    vmin=0,
                    vmax=vmax,
                    **kwargs
                )
                ax.set_title(f"{sample_id}_{gene}")
                ax.set_aspect('equal', adjustable='box')
            except Exception as e:
                print(f"Error plotting {gene} for sample {sample_id}: {str(e)}")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=dpi)

    return fig

