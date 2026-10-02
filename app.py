import os
import json
import streamlit as st

# Set Page Config
st.set_page_config(
    page_title="दैनिक समसामयिकी क्विज़ (Current Affairs)",
    page_icon="📚",
    layout="centered"
)

# Custom Styling for clean Hindi text presentation
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #1E88E5; text-align: center; }
    .sub-title { font-size: 18px; text-align: center; color: #555; }
    .question-box { font-size: 20px; font-weight: 600; margin-top: 15px; }
    .explanation-box { background-color: #f0f7ff; padding: 15px; border-radius: 8px; border-left: 5px solid #1E88E5; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

def load_quiz_files():
    """Finds all JSON quiz files in the current directory."""
    files = [f for f in os.listdir('.') if f.startswith('daily_quiz_hindi_') and f.endswith('.json')]
    files.sort(reverse=True)  # Latest quizzes first
    return files

def load_quiz_data(filename):
    """Loads JSON data for the selected date."""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

# Sidebar - Quiz Selection & Downloads
st.sidebar.title("📌 क्विज़ चयन (Select Quiz)")
quiz_files = load_quiz_files()

if not quiz_files:
    st.error("❌ कोई हिंदी क्विज़ फ़ाइल नहीं मिली! पहले `current.py` चलाकर JSON फ़ाइल जनरेट करें।")
    st.stop()

selected_file = st.sidebar.selectbox("दिनांक चुनें (Choose Date):", quiz_files)
quiz_data = load_quiz_data(selected_file)

# Sidebar Download Option for Raw Quiz JSON
st.sidebar.divider()
st.sidebar.subheader("📥 एक्सपोर्ट (Export Data)")
quiz_json_str = json.dumps(quiz_data, ensure_ascii=False, indent=4)
st.sidebar.download_button(
    label="📄 डाउनलोड क्विज़ JSON (Download Quiz JSON)",
    data=quiz_json_str,
    file_name=selected_file,
    mime="application/json"
)

# Initialize Session State Variables
if 'quiz_file' not in st.session_state or st.session_state.quiz_file != selected_file:
    st.session_state.quiz_file = selected_file
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.submitted_questions = set()
    st.session_state.quiz_completed = False

# Main Header
st.markdown('<div class="main-title">🎯 दैनिक समसामयिकी अभ्यास परीक्षा</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">दिनांक: <b>{quiz_data.get("quiz_date", "N/A")}</b> | कुल प्रश्न: <b>{len(quiz_data["questions"])}</b></div>',
    unsafe_allow_html=True
)
st.divider()

# Complete State View
if st.session_state.quiz_completed:
    st.balloons()
    st.success("🎉 परीक्षा पूरी हो गई है! (Quiz Completed!)")
    
    total = len(quiz_data["questions"])
    score = st.session_state.score
    percentage = round((score / total) * 100, 2)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("कुल प्रश्न (Total)", total)
    col2.metric("सही उत्तर (Correct)", score)
    col3.metric("सफलता दर (Score %)", f"{percentage}%")
    
    # Generate Printable/Exportable Performance Report in JSON format
    results_payload = {
        "quiz_date": quiz_data.get("quiz_date", "N/A"),
        "total_questions": total,
        "score_obtained": score,
        "accuracy_percentage": percentage,
        "user_performance": []
    }
    
    st.subheader("📋 परीक्षा का विस्तृत विश्लेषण (Detailed Review)")
    
    for idx, q in enumerate(quiz_data["questions"]):
        user_ans = st.session_state.user_answers.get(idx, "उत्तर नहीं दिया")
        correct_ans_key = q["correct_answer"]
        
        # Match correct text using key prefix or exact text
        correct_option_text = next((opt for opt in q["options"] if opt.startswith(correct_ans_key)), q["correct_answer"])
        is_correct = user_ans.startswith(correct_ans_key)

        results_payload["user_performance"].append({
            "question_no": idx + 1,
            "question": q["question"],
            "user_answer": user_ans,
            "correct_answer": correct_option_text,
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })
        
        with st.expander(f"प्रश्न {idx + 1}: {q['question']}"):
            if is_correct:
                st.success(f"✅ आपका उत्तर: {user_ans}")
            else:
                st.error(f"❌ आपका उत्तर: {user_ans}")
                st.info(f"✔ सही उत्तर: {correct_option_text}")
            
            st.markdown(f"**📖 परीक्षा व्याख्या (Explanation):**\n{q['explanation']}")
            
    st.divider()
    
    # Export Results Payload Button
    st.subheader("💾 परिणाम एक्सपोर्ट करें (Export Results)")
    report_json_str = json.dumps(results_payload, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 रिपोर्ट डाउनलोड करें (Download Results Report JSON)",
        data=report_json_str,
        file_name=f"quiz_result_{quiz_data.get('quiz_date', 'today')}.json",
        mime="application/json",
        type="primary"
    )
    
    if st.button("🔄 पुनः प्रयास करें (Restart Quiz)"):
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.user_answers = {}
        st.session_state.submitted_questions = set()
        st.session_state.quiz_completed = False
        st.rerun()

else:
    # Active Quiz State
    questions = quiz_data["questions"]
    curr_idx = st.session_state.current_index
    q = questions[curr_idx]
    
    # Progress Bar
    progress = (curr_idx + 1) / len(questions)
    st.progress(progress, text=f"प्रश्न {curr_idx + 1} / {len(questions)}")
    
    st.markdown(f'<div class="question-box">प्र. {curr_idx + 1}: {q["question"]}</div>', unsafe_allow_html=True)
    
    # Radio Choice Selection
    user_choice = st.radio(
        "सही विकल्प चुनें (Choose the correct option):",
        options=q["options"],
        key=f"q_{curr_idx}"
    )
    
    is_already_submitted = curr_idx in st.session_state.submitted_questions
    
    col1, col2 = st.columns([1, 1])
    
    if not is_already_submitted:
        if st.button("उत्तर की जांच करें (Submit Answer)", type="primary"):
            st.session_state.user_answers[curr_idx] = user_choice
            st.session_state.submitted_questions.add(curr_idx)
            
            correct_key = q["correct_answer"]
            if user_choice.startswith(correct_key):
                st.session_state.score += 1
            st.rerun()
    else:
        # Show Evaluation & Feedback
        user_ans = st.session_state.user_answers.get(curr_idx, user_choice)
        correct_key = q["correct_answer"]
        correct_text = next((opt for opt in q["options"] if opt.startswith(correct_key)), correct_key)

        if user_ans.startswith(correct_key):
            st.success("✨ बिल्कुल सही उत्तर! (Correct Answer)")
        else:
            st.error("❌ गलत उत्तर! (Incorrect Answer)")
            st.info(f"✔ सही उत्तर है: **{correct_text}**")
            
        st.markdown(f'<div class="explanation-box"><b>📖 व्याख्या (Exam Insight):</b><br>{q["explanation"]}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Navigation Actions
        if curr_idx + 1 < len(questions):
            if st.button("अगला प्रश्न ➔ (Next Question)", type="primary"):
                st.session_state.current_index += 1
                st.rerun()
        else:
            if st.button("परिणाम देखें 🏁 (View Results)", type="primary"):
                st.session_state.quiz_completed = True
                st.rerun()