import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, roc_curve, precision_recall_curve, auc
def confusion(y, p, labels, path, title):
    fig, ax = plt.subplots(figsize=(5.5, 5)); ConfusionMatrixDisplay.from_predictions(y, p, labels=labels, ax=ax, colorbar=False, xticks_rotation=45)
    ax.set_title(title); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
def roc_pr(curves, path, title):
    """curves: {name: (y_true, score)}"""
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for n, (y, s) in curves.items():
        f, t, _ = roc_curve(y, s); ax[0].plot(f, t, label=f"{n} (AUC {auc(f, t):.3f})")
        p, r, _ = precision_recall_curve(y, s); ax[1].plot(r, p, label=n)
    ax[0].plot([0, 1], [0, 1], "k:"); ax[0].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC"); ax[1].set(xlabel="Recall", ylabel="Precision", title="Precision-recall")
    ax[0].legend(fontsize=7); ax[1].legend(fontsize=7); fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
