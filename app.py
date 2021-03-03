from flask import Flask, render_template, request, redirect, url_for
import csv
import os
app = Flask(__name__)


def read_info():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(curr_dir, "static/subjects.csv")

    subjs_info = []

    with open(file_name, "r") as f:
        csvreader = csv.reader(f)
        for row in csvreader:
            subjs_info.append(row)

    return subjs_info[1:]


subjs_info = read_info()


def convert_score_to_grade(score):
    conversion_table = (
        (85, "A*"), (75, "A1"), (70, "A2"),
        (65, "B3"), (60, "B4"), (55, "C5"),
        (50, "C6"), (45, "D7"), (40, "E8"),
        (0, "F9")
    )

    for pair in conversion_table:
        if score >= pair[0]:
            grade = pair[1]
            return grade


def gpa_conv(grade):
    gpa_conv = {
        "A*": 5.0, "A1": 4.0, "A2": 3.5,
        "B3": 3.0, "B4": 2.5, "C5": 2.0,
        "C6": 1.5, "D7": 1.0, "E8": 0.5,
        "F9": 0.0
    }
    return gpa_conv[grade]


def sec4_gpa(subjs):
    best_sci = ["subj", 0]
    best_hum = ["subj", 0]

    for subj in subjs:
        if subj[2] == "Science" and subj[7] >= best_sci[1]:
            best_sci = [subj[1], subj[7]]
        elif subj[2] == "Humanities" and subj[7] >= best_hum[1] \
                and subj[1] != "ss":
            best_hum = [subj[1], subj[7]]

    best_other = ["subj", 0]

    for subj in subjs:
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

    for subj in subjs:
        if subj[1] in ["el", "hcl", "maths", "cid"] or \
                subj[1] in [best_sci[0], best_hum[0], best_other[0], ]:
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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/level_subjs/')
def level_subjs():
    level = request.args["level"]

    if level in "12":
        return redirect(url_for("gpa_calc", level=level))

    # print(subjs_info)

    compul_subjs = list(filter(
        lambda row: (level in row[3]) and (row[4] == "T"), subjs_info
    ))

    opt_subjs = list(filter(
        lambda row: (level in row[3]) and (row[4] == "F"), subjs_info
    ))

    print(level, compul_subjs, opt_subjs)

    return render_template(
        "level_subjs.html",
        level=level,
        compul_subjs=compul_subjs,
        opt_subjs=opt_subjs
    )


@app.route('/gpa_calc/', methods=["GET", "POST"])
def gpa_calc():
    if request.method == "GET":
        level = request.args["level"]
        subjs = []

        if level in "12":
            subjs = list(filter(
                lambda row: level in row[3], subjs_info
            ))
            # print(subjs)
        else:
            compul_subjs = list(filter(
                lambda row: (level in row[3]) and (row[4] == "T"), subjs_info
            ))

            selected_subjs = request.args.getlist("sci_subjs") + \
                request.args.getlist("hum_subjs")

            opt_subjs = list(filter(
                lambda row: (level in row[3]) and (
                    row[1] in selected_subjs), subjs_info
            ))

            subjs = compul_subjs + opt_subjs

            # print(subjs)
        return render_template("get_scores.html", level=level, subjs=subjs)
    else:
        # print(request.form)
        level = request.form["level"]
        selected_subjs = list(request.form.keys())
        selected_subjs.remove("level")

        subjs = []
        for row in subjs_info:
            if level in row[3] and row[1] in selected_subjs:
                subjs.append(row.copy())

        total_gpa = 0
        total_weight = 0

        for subj in subjs:
            score = int(request.form[subj[1]])
            grade = convert_score_to_grade(score)
            gpa = gpa_conv(grade)

            subj.append(score)
            subj.append(grade)
            subj.append(gpa)

            if subj[1] == "ss":
                total_gpa += gpa * 0.5
                total_weight += 0.5
            else:
                total_gpa += gpa
                total_weight += 1

        if level != "4":
            overall_gpa = round(total_gpa/total_weight, 2)
        else:
            overall_gpa = sec4_gpa(subjs)

        # print(subjs)

        return render_template(
            "result.html",
            subjs=subjs,
            overall_gpa=overall_gpa,
            level=level
        )


if __name__ == '__main__':
    app.run(debug=True)
