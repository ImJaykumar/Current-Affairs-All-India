import json
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(page_title="JSON to Excel Converter", layout="wide")

st.title("📊 Quiz JSON to Excel Converter")
st.write(
    "Upload one or multiple JSON quiz files to view, format, and download them as an Excel workbook."
)


def process_quiz_json(file_content):
    """Parses JSON content and converts it into a pandas DataFrame with split option columns."""
    data = json.load(file_content)

    quiz_date = data.get("quiz_date", "")
    state = data.get("state", "")
    language = data.get("language", "")
    questions = data.get("questions", [])

    rows = []
    for idx, q in enumerate(questions, start=1):
        raw_options = q.get("options", [])

        # Parse option array into individual Option A, B, C, D columns
        options_dict = {}
        for opt in raw_options:
            if opt.startswith("A)"):
                options_dict["Option A"] = opt.replace("A) ", "").strip()
            elif opt.startswith("B)"):
                options_dict["Option B"] = opt.replace("B) ", "").strip()
            elif opt.startswith("C)"):
                options_dict["Option C"] = opt.replace("C) ", "").strip()
            elif opt.startswith("D)"):
                options_dict["Option D"] = opt.replace("D) ", "").strip()

        row = {
            "Q. No.": idx,
            "Quiz Date": quiz_date,
            "State": state,
            "Language": language,
            "Question": q.get("question", ""),
            "Option A": options_dict.get("Option A", ""),
            "Option B": options_dict.get("Option B", ""),
            "Option C": options_dict.get("Option C", ""),
            "Option D": options_dict.get("Option D", ""),
            "Correct Answer": q.get("correct_answer", ""),
            "Explanation": q.get("explanation", ""),
        }
        rows.append(row)

    return pd.DataFrame(rows)


# File Uploader component (accepts multiple JSONs)
uploaded_files = st.file_uploader(
    "Choose JSON file(s)", type=["json"], accept_multiple_files=True
)

if uploaded_files:
    file_dfs = {}
    all_dfs = []

    # Process all uploaded JSON files
    for uploaded_file in uploaded_files:
        df = process_quiz_json(uploaded_file)
        clean_name = uploaded_file.name.rsplit(".", 1)[0]
        file_dfs[clean_name] = df
        all_dfs.append(df)

    # Combine all data into a master DataFrame
    combined_df = pd.concat(all_dfs, ignore_index=True)

    st.success(f"Successfully processed {len(uploaded_files)} file(s)!")

    # Interactive Data Preview
    st.subheader("📋 Data Preview")
    preview_option = st.selectbox(
        "Select sheet to preview:",
        options=["All Quizzes (Combined)"] + list(file_dfs.keys()),
    )

    if preview_option == "All Quizzes (Combined)":
        st.dataframe(combined_df, use_container_width=True)
    else:
        st.dataframe(file_dfs[preview_option], use_container_width=True)

    # Generate Excel file in memory using BytesIO
    import io

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        # 1. Master sheet containing all uploaded quizzes
        combined_df.to_excel(writer, index=False, sheet_name="All Quizzes")

        # 2. Individual sheet for each uploaded JSON
        for name, df in file_dfs.items():
            sheet_name = name[:31]  # Excel limit: max 31 characters
            df.to_excel(writer, index=False, sheet_name=sheet_name)

        # Apply cell formatting and text wrapping across sheets
        workbook = writer.book
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for col in worksheet.columns:
                max_len = 0
                col_letter = col[0].column_letter

                for cell in col:
                    cell.alignment = cell.alignment.copy(
                        wrap_text=True, vertical="top"
                    )
                    val_str = str(cell.value or "")
                    max_len = max(max_len, len(val_str))

                worksheet.column_dimensions[col_letter].width = min(
                    max(max_len + 3, 12), 50
                )

    excel_data = excel_buffer.getvalue()

    # Download Button
    st.download_button(
        label="📥 Download Excel Workbook (.xlsx)",
        data=excel_data,
        file_name="quiz_questions_converted.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )