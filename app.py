from flask import Flask, render_template, request, redirect, url_for
import csv
import os


app = Flask(__name__)


# Helper functions


def read_info():
    subjs_info = []
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(curr_dir, "static/data/subjects.csv")

    with open(file_name, "r") as f:
        csvreader = csv.reader(f)
        _ = next(csvreader)  # remove header line

        for row in csvreader:
            subjs_info.append(row)

    return subjs_info


subjs_info = read_info()


def score_to_grade_gpa(score):
    matrix = {
        85: ("A*", 5.0), 75: ("A1", 4.0), 70: ("A2", 3.5),
        65: ("B3", 3.0), 60: ("B4", 2.5), 55: ("C5", 2.0),
        50: ("C6", 1.5), 45: ("D7", 1.0), 40: ("E8", 0.5),
        0: ("F9", 0.0)
    }
    for cutoff_point in matrix:
        if score >= cutoff_point:
            return matrix[cutoff_point]


def normal_gpa(subjs):
    # this will simply calculate average gpa for all subjs for sec 1 to 3
    total_gpa = 0
    total_weightage = 0

    for row in subjs:
        if row[1] == "ss":
            total_gpa += row[-1] * 0.5
            total_weightage += 0.5
        else:
            total_gpa += row[-1]
            total_weightage += 1.0

    return round(total_gpa / total_weightage, 2)


def sec4_gpa(user_subjs):
    best_sci = ["subj", 0]
    best_hum = ["subj", 0]
    best_other = ["subj", 0]

    for subj in user_subjs:
        if subj[2] == "Science" and subj[7] >= best_sci[1]:
            best_sci = [subj[1], subj[7]]
        elif subj[2] == "Humanities" and subj[7] >= best_hum[1] \
                and subj[1] != "ss":
            best_hum = [subj[1], subj[7]]

    for subj in user_subjs:
        if subj[2] == "Science" and subj[1] != best_sci[0] \
                and subj[7] >= best_other[1]:
            best_other = [subj[1], subj[7]]
        elif subj[2] == "Humanities" and subj[1] != best_hum[0] \
                and subj[7] >= best_other[1] and subj[1] != "ss":
            best_other = [subj[1], subj[7]]
        elif subj[2] == "Maths" and subj[7] >= best_other[1]:
            best_other = [subj[1], subj[7]]

    total_gpa = 0
    total_weight = 0

    for subj in user_subjs:
        if subj[1] in ["el", "hcl", "maths", "cid"] or \
                subj[1] in [best_sci[0], best_hum[0], best_other[0]]:
            total_gpa += subj[7]
            total_weight += 1
            if best_other[0] == "maths" and subj[1] == "maths":
                subj.append("D")
            else:
                subj.append("C")
        elif subj[1] == "ss":
            total_gpa += subj[7] * 0.5
            total_weight += 0.5
            subj.append("C")
        else:
            subj.append("U")

    return round(total_gpa/total_weight, 2)


# Flask functions


@app.route('/')
def index():
    return render_template('p1_index.html', level=1)


@app.route('/subjs_selection/')
def subjs_selection():
    level = request.args["level"]

    if level in "12":
        # user selected sec 1 or 2
        return redirect(url_for("gpa_calc", level=level))
    else:
        # user selected sec 3 or 4
        compul_subjs = []
        opt_sci_subjs = []
        opt_hum_subjs = []

        for row in subjs_info:
            if level in row[3] and row[4] == "T":
                # this subj is compulsory for this level
                compul_subjs.append(row)
            elif level in row[3] and row[2] == "Science" and row[4] == "F":
                # this sci subj is optional for this level
                opt_sci_subjs.append(row)
            elif level in row[3] and row[2] == "Humanities" and row[4] == "F":
                # this hum subj is optional for this level
                opt_hum_subjs.append(row)

        return render_template(
            "p2_subjs_selection.html", level=level, compul_subjs=compul_subjs,
            opt_sci_subjs=opt_sci_subjs, opt_hum_subjs=opt_hum_subjs
        )


@app.route('/gpa_calc/', methods=["GET", "POST"])
def gpa_calc():
    if request.method == "GET":
        level = request.args["level"]
        user_subjs = []

        if level in "12":
            # sec 1 or 2
            for row in subjs_info:
                if level in row[3]:
                    # all subjs are compulsory for sec 1&2
                    user_subjs.append(row)

            opt_sci_subjs = []
            opt_hum_subjs = []
        else:
            # sec 3 or 4
            opt_sci_subjs = request.args.getlist("opt_sci_subjs")
            opt_hum_subjs = request.args.getlist("opt_hum_subjs")
            # print(sci_subjs, hum_subjs)
            for row in subjs_info:
                if level in row[3] and row[4] == "T":
                    # this subj is compulsory for this level
                    user_subjs.append(row)
                elif row[1] in opt_sci_subjs or row[1] in opt_hum_subjs:
                    # this optional subj is selected by user
                    user_subjs.append(row)

            # print(subjs)
        return render_template(
            "p3_scores_entry.html", level=level, user_subjs=user_subjs,
            opt_sci_subjs=opt_sci_subjs, opt_hum_subjs=opt_hum_subjs,
        )
    else:
        # process the subjs data
        level = request.form["level"]

        user_subjs = []
        opt_sci_subjs = []
        opt_hum_subjs = []

        for key in request.form:
            for row in subjs_info:
                if row[1] == key:
                    new_row = row.copy()
                    # append the score of the subj to the new list
                    new_row.append(int(request.form[key]))
                    # add the subj info with score to subjs
                    user_subjs.append(new_row)
                    # only 1 subj will match the condition
                    break

        # print(subjs)

        # process the score to grade and gpa
        for row in user_subjs:
            if row[4] == "F" and row[2] == "Science":
                opt_sci_subjs.append(row[1])
            elif row[4] == "F" and row[2] == "Humanities":
                opt_hum_subjs.append(row[1])

            # print(row)
            # print(score_to_grade_gpa(row[-1]))
            grade, gpa = score_to_grade_gpa(row[-1])

            row.append(grade)
            row.append(gpa)

        # print(subjs)
        if level in "123":
            gpa = normal_gpa(user_subjs)
        else:
            gpa = sec4_gpa(user_subjs)

        # print(user_subjs, gpa)
        return render_template(
            "p4_result.html", level=level, subjs=user_subjs, gpa=gpa,
            opt_sci_subjs=opt_sci_subjs, opt_hum_subjs=opt_hum_subjs
        )


if __name__ == '__main__':
    app.run(debug=True)
