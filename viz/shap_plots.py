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
            return plt.figure()

        explainer = explainers.get(input.mold_code())
        if explainer is None:
            return plt.figure()

        shap.initjs()
        shap.force_plot(
            base_value=explainer.expected_value,
            shap_values=shap_values.values[0],
            features=X.iloc[0, :],
            matplotlib=True,
            show=False
        )
        plt.rcParams.update({"font.size": 8})
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

        shap.summary_plot(shap_values.values, X, show=False)
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
