# Re-run the CDS-dependent analyses of 1_modeling.Rmd with faulty vs corrected tCDS labels.
#
# The code below does not re-implement the analyses: it extracts the relevant chunks from
# 1_modeling.Rmd and evaluates them as written, swapping only the two input files that depend on
# the tCDS classifier (everyday_cds_ods.csv and the burstiness file).
#
# Two changes are needed to run the chunks today; neither changes a result:
#   * summarize() returning several rows per group is an error in dplyr >= 1.2; it is replaced by
#     reframe(), which is what summarize() did in the dplyr version used for the paper (1.1.3).
#   * The setup chunk is skipped (it loads stargazer and effects, which are only used for LaTeX
#     tables and effect plots); the packages the analysis chunks need are loaded here.
#
# The 'read in LENA data' chunk now filters everyday_cds_ods.csv to cds_pred == 1 (restored upstream
# in 793f13c). With that filter, hourly words (the 'quantity' covariate) count CDS epochs only, and
# the Sec 3.2 descriptives degenerate ("% CDS epochs" is 100% by construction). The published
# numbers (Table 2: 1094 words/hr; quantity chi2 = 0.35; vocab chi2 = 4.42 and 4.12) are reproduced
# only without the filter, i.e. with hourly words over all awake epochs. So every condition is run
# both ways (`quantity` column):
#   all_awake_words  chunk without the filter line, as the published results were computed
#   cds_words        chunk as currently written; hourly words then also depend on the classifier
# The descriptives (desc_*) always come from the unfiltered chunk.
#
# Run from the repo root, after `python reclassify_tcds.py apply` and burst_detection_v2.py:
#   Rscript rerun_tcds_analysis.R
# The demographics chunk writes dataframes/romeo_demo.csv and dataframes/l2t_demo.csv, as when
# knitting 1_modeling.Rmd. Burst files are copied to a temporary directory, nothing else is written.

suppressMessages({
  library(tidyverse); library(lme4); library(lmerTest); library(lubridate)
  library(zoo); library(knitr); library(kableExtra)
})

stopifnot(file.exists("1_modeling.Rmd"), file.exists("dataframes/everyday_cds_ods.csv"))
tmp <- file.path(tempdir(), "tcds_rerun")
dir.create(tmp, showWarnings = FALSE)

# ---- extract chunks from 1_modeling.Rmd by label ----
rmd <- readLines("1_modeling.Rmd")
chunk <- function(label) {
  start <- grep(paste0("^```\\{r,? *", label, "[,}]"), rmd)
  stopifnot(length(start) == 1)
  end <- start + which(grepl("^```\\s*$", rmd[(start + 1):length(rmd)]))[1]
  rmd[(start + 1):(end - 1)]
}
run <- function(code, env) eval(parse(text = code), envir = env)
swap <- function(code, from, to) {
  stopifnot(sum(grepl(from, code, fixed = TRUE)) == 1)
  sub(from, to, code, fixed = TRUE)
}

# demographics (does not depend on the classifier)
base_env <- new.env()
run(chunk("read in demographic and score info"), base_env)

# the CDS part of the 'read in LENA data' chunk (the ctc/speech parts are not needed here)
lena <- chunk("read in LENA data")
cds_code <- lena[grep("^pre_pre_cds <-", lena):length(lena)]
cds_code <- swap(cds_code, "summarize(percen_cds_epochs", "reframe(percen_cds_epochs")
cds_filter <- grep("filter(cds_pred=='1') %>% # select only those epochs", cds_code, fixed = TRUE)
stopifnot(length(cds_filter) == 1)
cds_code_unfiltered <- cds_code[-cds_filter]

analysis_code <- c(
  chunk("compute burstiness of cds using neurodsp measures"),
  chunk("make recording stat table"),
  chunk("model relationship between age and cds burstiness"),
  chunk("model relationship between cds burstiness and vocabulary")
)

conditions <- tribble(
  ~condition,                     ~cds_file,                                       ~burst_file,
  "paper (shipped burst file)",   "dataframes/everyday_cds_ods.csv",               "dataframes/burstiness_compiled_results.csv",
  "faulty labels, 3*SD",          "dataframes/everyday_cds_ods.csv",               "tcds_rerun/burstiness_faulty_labels_3sd.csv",
  "corrected labels, 3*SD",       "dataframes/everyday_cds_ods_reclassified.csv",  "tcds_rerun/burstiness_corrected_labels_3sd.csv",
  "faulty labels, mean+3*SD",     "dataframes/everyday_cds_ods.csv",               "tcds_rerun/burstiness_faulty_labels_mean3sd.csv",
  "corrected labels, mean+3*SD",  "dataframes/everyday_cds_ods_reclassified.csv",  "tcds_rerun/burstiness_corrected_labels_mean3sd.csv"
)

results <- list()
for (quantity in c("all_awake_words", "cds_words")) for (i in seq_len(nrow(conditions))) {
  cond <- conditions[i, ]
  cat("\n==", quantity, "|", cond$condition, "\n")
  # children with no bursts have no burst length/amplitude; drop them up front so baseline and
  # burst models are fit to the same rows (otherwise anova() errors). The shipped file has none.
  bursts <- read.csv(cond$burst_file)
  n_no_bursts <- sum(is.na(bursts$mean_burst_length))
  burst_path <- file.path(tmp, paste0("burst_", i, ".csv"))
  write.csv(filter(bursts, !is.na(mean_burst_length)), burst_path, row.names = FALSE)

  desc_env <- new.env(parent = base_env)
  run(swap(cds_code_unfiltered, "'dataframes/everyday_cds_ods.csv'", deparse(cond$cds_file)), desc_env)

  env <- new.env(parent = base_env)
  model_cds_code <- if (quantity == "cds_words") cds_code else cds_code_unfiltered
  run(swap(model_cds_code, "'dataframes/everyday_cds_ods.csv'", deparse(cond$cds_file)), env)
  run(swap(analysis_code, "'dataframes/burstiness_compiled_results.csv'", deparse(burst_path)), env)

  with(env, {
    coef_row <- function(s) s$coefficients[2, ]
    results[[paste(quantity, cond$condition)]] <<- tibble(
      quantity = quantity,
      condition = cond$condition,
      dropped_no_bursts = n_no_bursts,
      recordings = n_distinct(burst_df2$child_id),
      children = n_distinct(burst_df2$ResearchID),
      desc_cds_prob_mean = desc_env$cds_stats$mean_cds_prob, desc_cds_prob_sd = desc_env$cds_stats$sd_cds_prob,
      desc_pct_cds_epochs = 100 * desc_env$cds_perc$mean_percen_cds,
      burst_amp_mean = mean(burst_df2$mean_burst_amplitude),
      burst_len_mean = mean(burst_df2$mean_burst_length),
      hrly_words_mean = mean(burst_df2$avg_hrly_words),
      age_amp_chisq = amp_test$Chisq[2], age_amp_p = amp_test$`Pr(>Chisq)`[2],
      age_amp_beta = coef_row(burst_amp_sum)[["Estimate"]], age_amp_beta_p = coef_row(burst_amp_sum)[["Pr(>|t|)"]],
      age_dur_chisq = duration_test$Chisq[2], age_dur_p = duration_test$`Pr(>Chisq)`[2],
      age_dur_beta = coef_row(burst_length_sum)[["Estimate"]], age_dur_beta_p = coef_row(burst_length_sum)[["Pr(>|t|)"]],
      age_quant_chisq = quant_test$Chisq[2], age_quant_p = quant_test$`Pr(>Chisq)`[2],
      vocab_n = nobs(burst_amp_v),
      vocab_amp_chisq = amp_test_v$Chisq[2], vocab_amp_p = amp_test_v$`Pr(>Chisq)`[2],
      vocab_amp_beta = coef_row(burst_amp_v_sum)[["Estimate"]], vocab_amp_beta_p = coef_row(burst_amp_v_sum)[["Pr(>|t|)"]],
      vocab_dur_chisq = duration_test_v$Chisq[2], vocab_dur_p = duration_test_v$`Pr(>Chisq)`[2],
      vocab_dur_beta = coef_row(burst_length_v_sum)[["Estimate"]], vocab_dur_beta_p = coef_row(burst_length_v_sum)[["Pr(>|t|)"]]
    )
  })
}

out <- bind_rows(results)
write.csv(out, "tcds_rerun/results.csv", row.names = FALSE)
print(as.data.frame(out %>% mutate(across(where(is.numeric), ~ signif(.x, 4)))) %>% t())
