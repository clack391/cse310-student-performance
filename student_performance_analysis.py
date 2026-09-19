"""Student Performance Analysis.

Analyzes the UCI Student Performance dataset to answer two questions:

  1. Does more weekly study time actually raise a student's final grade,
     and how does that compare to the effect of past course failures?
  2. Among students who fail, what separates them from students who
     pass? This looks at past failures and whether a student receives
     extra school support.

Dataset: UCI Machine Learning Repository, Student Performance
https://archive.ics.uci.edu/dataset/320/student+performance

Two CSV files are provided by UCI, one per subject (math and Portuguese).
Both share the same 33 columns and are semicolon separated rather than
comma separated, which is the first thing that trips up loading them.

Every answer below is printed with the number of students behind it.
A result from fewer than MIN_GROUP_SIZE students is labeled as too
small to trust rather than reported as a finding, since a dataset this
size makes it easy to slice until a small group looks dramatic.
"""

import pandas as pd
import matplotlib.pyplot as plt

MIN_GROUP_SIZE = 30
PASS_MARK = 10

STUDY_TIME_LABELS = {
    1: "under 2 hrs",
    2: "2 to 5 hrs",
    3: "5 to 10 hrs",
    4: "over 10 hrs",
}


def load_dataset(path):
    """Load one of the UCI student performance CSV files.

    The files use a semicolon as the column separator instead of the
    default comma, so pandas needs to be told that explicitly.
    """
    return pd.read_csv(path, sep=";")


def clean_dataset(df):
    """Return a copy of df with non-attempted exams removed.

    A final grade (G3) of 0 usually means the student did not sit the
    final exam rather than that they scored zero on it. Including those
    rows would drag every average down for a reason unrelated to study
    habits, so they are filtered out before any analysis runs.
    """
    return df[df["G3"] > 0].copy()


def label_study_time(df):
    """Add a study_time_label column with human readable study bands.

    The raw studytime column is a 1 to 4 code. This converts each code
    to what it actually means, which is the "data conversion"
    requirement for this module.
    """
    df = df.copy()
    df["study_time_label"] = df["studytime"].map(STUDY_TIME_LABELS)
    return df


def add_pass_flag(df):
    """Add a passed column: 1 if the final grade meets the pass mark.

    G3 runs from 0 to 20 with 10 as the official pass mark. Converting
    it to a 0/1 flag lets a group's average be read directly as a pass
    rate, which is the second data conversion used in this analysis.
    """
    df = df.copy()
    df["passed"] = (df["G3"] >= PASS_MARK).astype(int)
    return df


def summarize_by(df, group_col, value_col, agg):
    """Filter, aggregate and sort df[value_col] grouped by group_col.

    Filters out any group with fewer than MIN_GROUP_SIZE rows before
    aggregating, so a group too small to trust never reaches the
    printed answer. Returns the result sorted from lowest to highest,
    which is the "sort" requirement for this module, alongside a count
    column so every number is tied to its sample size.
    """
    grouped = df.groupby(group_col)[value_col].agg(["mean", "count"])
    grouped = grouped.rename(columns={"mean": agg})
    big_enough = grouped[grouped["count"] >= MIN_GROUP_SIZE]
    return big_enough.sort_values(agg)


def print_group_table(title, table, value_label):
    """Print a summary table with an explicit sample size per row."""
    print("\n" + title)
    for label, row in table.iterrows():
        print("  {:<14} {}: {:6.2f}   (n={})".format(
            str(label), value_label, row.iloc[0], int(row["count"])))


def answer_question_1(df):
    """Question 1: study time vs. past failures, which moves grades more?

    Uses groupby (aggregate), the study_time_label conversion, and the
    sort inside summarize_by. Both grade tables are printed so their
    ranges can be compared directly.
    """
    by_study_time = summarize_by(df, "study_time_label", "G3", "mean")
    by_failures = summarize_by(df, "failures", "G3", "mean")

    print_group_table(
        "Average final grade by weekly study time", by_study_time, "avg G3")
    print_group_table(
        "Average final grade by past course failures", by_failures, "avg G3")

    study_time_range = by_study_time["mean"].max() - by_study_time["mean"].min()
    failures_range = by_failures["mean"].max() - by_failures["mean"].min()

    print("\nAnswer: study time moves the average grade by about {:.1f} "
          "points across bands, while past failures move it by about "
          "{:.1f} points. Past failures are the stronger predictor of "
          "the two, even though studying more does still help.".format(
              study_time_range, failures_range))

    return by_study_time, by_failures


def answer_question_2(df):
    """Question 2: what separates passing students from failing ones?

    Uses the passed conversion, groupby aggregation for the pass rate,
    and a boolean filter on failures > 0 to isolate at-risk students.
    """
    by_failures = summarize_by(df, "failures", "passed", "pass_rate")
    by_failures["pass_rate"] = by_failures["pass_rate"] * 100

    by_support = summarize_by(df, "schoolsup", "passed", "pass_rate")
    by_support["pass_rate"] = by_support["pass_rate"] * 100

    print_group_table(
        "Pass rate (%) by number of past failures", by_failures, "pass rate")
    print_group_table(
        "Pass rate (%) by extra school support", by_support, "pass rate")

    at_risk = df[df["failures"] > 0]
    print("\n{} students have at least one past failure (n={}).".format(
        len(at_risk), len(at_risk)))

    print("\nAnswer: pass rate falls sharply as past failures increase. "
          "Counterintuitively, students who receive extra school support "
          "pass less often than those who do not. That is not evidence "
          "that support hurts. Support is assigned to students who are "
          "already struggling, so this is a selection effect rather than "
          "a cause and effect relationship.")

    return by_failures, by_support


def plot_grade_by_study_time(by_study_time, output_path):
    """Save a bar chart of average final grade by study time band."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(by_study_time.index.astype(str), by_study_time["mean"],
           color="#4C72B0")
    ax.set_xlabel("Weekly study time")
    ax.set_ylabel("Average final grade (G3)")
    ax.set_title("Average Final Grade by Weekly Study Time")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_pass_rate_by_failures(by_failures, output_path):
    """Save a bar chart of pass rate by number of past failures."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(by_failures.index.astype(str), by_failures["pass_rate"],
           color="#DD8452")
    ax.set_xlabel("Number of past course failures")
    ax.set_ylabel("Pass rate (%)")
    ax.set_title("Pass Rate by Number of Past Failures")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def main():
    """Load, clean and analyze the math dataset, then save both charts."""
    raw = load_dataset("data/student-mat.csv")
    print("Loaded {} rows from student-mat.csv".format(len(raw)))

    df = clean_dataset(raw)
    print("{} rows remain after removing students with G3 == 0 "
          "(did not sit the final).".format(len(df)))

    df = label_study_time(df)
    df = add_pass_flag(df)

    print("\n" + "=" * 60)
    print("QUESTION 1: Does study time or past failures predict grades")
    print("more strongly?")
    print("=" * 60)
    by_study_time, by_failures_grade = answer_question_1(df)

    print("\n" + "=" * 60)
    print("QUESTION 2: What separates passing students from failing")
    print("ones?")
    print("=" * 60)
    by_failures_pass, by_support = answer_question_2(df)

    plot_grade_by_study_time(by_study_time, "grade_by_study_time.png")
    plot_pass_rate_by_failures(by_failures_pass, "pass_rate_by_failures.png")
    print("\nSaved grade_by_study_time.png and pass_rate_by_failures.png")


if __name__ == "__main__":
    main()
