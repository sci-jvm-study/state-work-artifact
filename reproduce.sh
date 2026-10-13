#!/bin/bash
# Regenerates every file in results/ from the data in this package. Run from the package root: bash reproduce.sh [outdir]
# Needs Python with analysis/requirements.txt and a JDK `javac` on PATH (static-feature step). Output goes to outdir (default results_new/).
set -e
cd "$(dirname "$0")"
O=${1:-results_new}; mkdir -p "$O"; O=$(cd "$O" && pwd)
cd analysis
python fit_construct_validation.py > "$O"/01_construct_validation.txt
python models_m1_to_m5.py > "$O"/02_models_m1_to_m5.txt
python fit_hybrid_model.py > "$O"/04_model_m6_and_gated.txt
python fit_nested_cv_rf_tuning.py > "$O"/05_nested_cv_rf_tuning.txt
python fit_all_baselines_fair_comparison.py > "$O"/06_baselines_fair_comparison.txt
python fit_baselines_per_family.py > "$O"/07_baselines_per_family.txt
python fit_generalization_splits.py > "$O"/09_generalization_splits.txt
python fit_knuth_online_cost_analysis.py > "$O"/14_knuth_online_cost.txt
python fit_m6_imputation_comparison.py > "$O"/15_m6_imputation_comparison.txt
python fit_node_count_baseline.py > "$O"/16_node_count_vs_work.txt
python fit_knuth_matched_population.py > "$O"/17_knuth_matched_population.txt
python paired_tests_group_c.py > "$O"/29_paired_tests_group_c.txt
python work_ratio_check.py > "$O"/32_work_ratio.txt
python corpus_subset_check.py > "$O"/34_pre_extension_subset.txt
python floor_by_cost_measure.py > "$O"/37_floor_by_cost_measure.txt
python calibration_analysis.py > "$O"/38_calibration.txt
python heldout_eval.py > "$O"/40_heldout_evaluation.txt
python heldout_eval_other_engines.py jpf > "$O"/57_heldout_other_engines_jpf.txt
python heldout_eval_other_engines.py coastal > "$O"/58_heldout_other_engines_coastal.txt
python heldout_eval_other_engines.py gdart > "$O"/59_heldout_other_engines_gdart.txt
python heldout_feature_overlap.py > "$O"/41_heldout_feature_overlap.txt
python nesting_decomposition.py > "$O"/44_nesting_decomposition.txt   # also writes ../results/44_nesting_decomposition_groups.csv
(for n in 30 5 1; do echo "##### probes per unit = $n"; python load_balance_probe_cost.py 4 $n; done) > "$O"/45_load_balance_probe_cost.txt
python nesting_consistency.py > "$O"/46_nesting_consistency.txt
python nesting_offline.py > "$O"/47_nesting_offline.txt
python nesting_offline_groups_csv.py                         # writes ../results/47_nesting_offline_groups.csv
python depth_rule.py > "$O"/60_depth_rule.txt
python zero_work_states.py > "$O"/61_zero_work_states.txt
KEEP_PRUNED_CHOICES=1 python zero_work_sensitivity.py > "$O"/62_zero_work_sensitivity.txt
KEEP_PRUNED_CHOICES=1 python zero_work_sensitivity_history.py > "$O"/63_zero_work_sensitivity_history.txt
KEEP_PRUNED_CHOICES=1 DROP_ZERO_WORK=1 python zero_work_sensitivity_history.py > "$O"/63b_zero_work_dropped_history.txt
KEEP_PRUNED_CHOICES=1 python zero_work_sensitivity_baselines.py > "$O"/64_zero_work_sensitivity_baselines.txt
python depth_rule_49.py > "$O"/65_depth_rule_49.txt
echo >> "$O"/65_depth_rule_49.txt
KEEP_PRUNED_CHOICES=1 python depth_rule_49.py >> "$O"/65_depth_rule_49.txt
python non_nested_pairs.py > "$O"/66_non_nested_pairs.txt
python probing_seed_sensitivity.py > "$O"/71_probing_seed_sensitivity.txt
REMOVE_PRUNED_CHOICES=1 python fit_knuth_matched_population.py > "$O"/69_knuth_pruned_removed.txt
python ../larger_trees/eval_large.py > "$O"/70_larger_trees.txt
(for u in 4 2 8; do echo "##### units per worker = $u (cut level needs >= $u*K non-leaf states)"; python load_balance_replay.py $u; done) > "$O"/39_load_balance_replay.txt
cd ../engines
python compile_bins.py
python final_table.py exact > "$O"/18_cross_engine_estimators.txt
python validate_static.py > "$O"/21_static_feature_port_validation.txt
cd ../analysis
python cross_engine_models.py --coastal data_coastal2 --also data_coastal2_BF > "$O"/19_cross_engine_models_dfs.txt
python cross_engine_models.py --coastal data_coastal2_BF --also data_coastal2 > "$O"/20_cross_engine_models_bfs.txt
python cross_engine_replication.py --coastal data_gdart --subset exact --work full > "$O"/27_gdart_replication.txt
python cross_engine_cost_and_cap.py > "$O"/52_cross_engine_cost_and_cap.txt
python cross_engine_load_balance.py > "$O"/53_cross_engine_load_balance.txt
# reads the result files 18, 19, 20, 29, 39 and 45, so it runs after them
RESULTS_DIR="$O" python multiple_comparison_correction.py > "$O"/51_multiple_comparison_correction.txt
cd ../live_estimator
python overhead_analysis.py > results/h2_overhead.txt   # the other live-check scripts are described in live_estimator/README.md
cd ..
cd figures && python make_figures.py
echo DONE
