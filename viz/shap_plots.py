import shap
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance
from shiny import render, reactive

def register_shap_plots(output, shap_values_state, X_input_state, y_test_state, models, explainers, input):
    """
    SHAP Force Plot / Summary Plot / Permutation Importance 등록
    """

    # -----------------------
    # 1. Force Plot (개별 샘플)
    # -----------------------
    @output
    @render.plot
    @reactive.event(input.btn_predict)
    def shap_force_plot():
        shap_values = shap_values_state.get()
        X = X_input_state.get()
        if shap_values is None or X is None:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "⚠️ SHAP 값 없음", ha="center", va="center", fontsize=12)
            ax.axis("off")
            return fig

        explainer = explainers.get(input.mold_code())
        if explainer is None:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "⚠️ Explainer 없음", ha="center", va="center", fontsize=12)
            ax.axis("off")
            return fig

        # ✅ expected_value 정리 (배열일 경우 첫 원소만 사용)
        base_value = explainer.expected_value
        if isinstance(base_value, (list, tuple)) or hasattr(base_value, "__len__"):
            base_value = base_value[0]

        # ✅ shap values → 클래스 1 기준 추출
        shap_vals = shap_values.values[0]
        if shap_vals.ndim == 2 and shap_vals.shape[1] == 2:
            shap_vals = shap_vals[:, 1]

        # ✅ 최신 shap API 사용
        plt.figure()
        shap.plots.force(
            base_value,
            shap_vals,
            X.iloc[0, :]
        )
        plt.tight_layout()
        return plt.gcf()

    # -----------------------
    # 2. Summary Plot (전체 샘플)
    # -----------------------
    @output
    @render.plot
    def shap_summary_plot():
        shap_values = shap_values_state.get()
        X = X_input_state.get()
        if shap_values is None or X is None:
            return plt.figure()

        shap.summary_plot(
            shap_values.values[:, :, 1] if shap_values.values.ndim == 3 else shap_values.values,
            X,
            show=False
        )
        return plt.gcf()

    # -----------------------
    # 3. Permutation Importance
    # -----------------------
    @output
    @render.plot
    def permutation_importance_plot():
        mold_code = input.mold_code()
        model = models.get(mold_code)
        X = X_input_state.get()
        y = y_test_state.get()

        if model is None or X is None or y is None:
            return plt.figure()

        result = permutation_importance(
            model, X, y,
            n_repeats=10,
            random_state=42,
            n_jobs=-1
        )
        sorted_idx = result.importances_mean.argsort()

        plt.barh(X.columns[sorted_idx], result.importances_mean[sorted_idx])
        plt.xlabel("Permutation Importance")
        plt.title("Permutation Importance (전체 데이터)")
        return plt.gcf()
