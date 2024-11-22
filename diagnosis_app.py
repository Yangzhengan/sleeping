# @Author : Yzg
# @File   : diagnosis_app.py
# @Time   : 2024/11/21 14:11
import streamlit as st
import json
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置为微软雅黑或其他支持中文的字体x
rcParams['axes.unicode_minus'] = False  # 防止负号显示为方块


# 加载知识图谱函数
def load_knowledge_graph(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 根据症状获取诊断
def get_diagnosis(symptoms, knowledge_graph):
    possible_diagnoses = []

    # 遍历每个睡眠障碍（每个元素是一个字典）
    for disorder in knowledge_graph:
        # 判断症状是否匹配
        if all(symptom in disorder["symptom"] for symptom in symptoms):
            possible_diagnoses.append({
                "疾病": disorder["name"],  # 获取疾病名称
                "诊断标准": disorder["diag_criteria"],  # 获取诊断标准
                "治疗建议": disorder["cure_way"],  # 获取治疗建议
            })

    return possible_diagnoses


# 主函数
def main():
    st.set_page_config(page_title="疾病诊断系统", layout="wide")

    # 加载知识图谱
    file_path = r"D:\Pythonproject\LearningPython\sleep_konwledge_graph.json"
    knowledge_graph = load_knowledge_graph(file_path)

    # 页面导航
    menu = ["首页", "逐步引导", "症状选择", "诊断结果", "反馈", "隐私管理"]
    choice = st.sidebar.selectbox("导航", menu)

    if choice == "首页":
        st.title("欢迎使用疾病诊断系统")
        st.markdown("""
        **功能简介：**
        - 根据症状选择进行疾病诊断。
        - 提供诊断结果及治疗建议。
        - 支持数据可视化及用户反馈。
        """)
        st.info("隐私声明：本系统仅在会话中保存您的数据，所有输入均不会上传到服务器或外部存储。")
    elif choice == "逐步引导":
        st.title("逐步引导模式")

        # 第一步：选择症状
        step = st.radio("请选择步骤：", ["选择症状", "确认症状", "查看结果"])
        if step == "选择症状":
            st.subheader("第1步：选择您的症状")
            all_symptoms = set()
            for disorder in knowledge_graph:
                all_symptoms.update(disorder["symptom"])
            selected_symptoms = st.multiselect("选择症状：", list(all_symptoms))
            if st.button("保存症状"):
                st.session_state["selected_symptoms"] = selected_symptoms
                st.success("症状已保存，请前往下一步。")

        # 第二步：确认症状
        elif step == "确认症状":
            st.subheader("第2步：确认选择的症状")
            if "selected_symptoms" in st.session_state:
                st.write("您选择的症状：", st.session_state["selected_symptoms"])
                if st.button("确认并继续"):
                    st.session_state["confirmed"] = True
                    st.success("症状确认成功！请前往下一步。")
            else:
                st.warning("请先选择症状。")

        # 第三步：查看结果
        elif step == "查看结果":
            st.subheader("第3步：诊断结果")
            if "confirmed" in st.session_state and st.session_state["confirmed"]:
                diagnoses = get_diagnosis(st.session_state["selected_symptoms"], knowledge_graph)
                if diagnoses:
                    for diag in diagnoses:
                        st.markdown(f"### {diag['疾病']}")
                        st.markdown(f"**诊断标准：** {diag['诊断标准']}")
                        st.markdown(f"**治疗建议：** {diag['治疗建议']}")
                else:
                    st.warning("未找到符合条件的疾病。")
            else:
                st.warning("请先完成症状确认。")
    elif choice == "症状选择":
        st.header("症状选择")
        st.markdown("请根据您的情况选择症状：")

        # 获取所有症状
        all_symptoms = set()

        # 遍历知识图谱中的每个睡眠障碍对象（每个对象是一个字典）
        for disorder in knowledge_graph:
            # 获取每个障碍的症状，并将其更新到 all_symptoms 集合中
            all_symptoms.update(disorder["symptom"])

        # 症状选择
        selected_symptoms = st.multiselect("选择症状", list(all_symptoms))

        if st.button("保存症状"):
            st.session_state["symptoms"] = selected_symptoms
            st.success("症状已保存！")
    elif choice == "诊断结果":
        st.header("诊断结果")
        if "symptoms" in st.session_state and st.session_state["symptoms"]:
            selected_symptoms = st.session_state["symptoms"]
            diagnoses = get_diagnosis(selected_symptoms, knowledge_graph)

            if diagnoses:
                st.write("以下是根据您选择的症状生成的诊断结果：")
                for diag in diagnoses:
                    st.markdown(f"### {diag['疾病']}")
                    st.markdown(f"**诊断标准：** {diag['诊断标准']}")
                    st.markdown(f"**治疗建议：** {diag['治疗建议']}")

                # 数据可视化
                st.write("#### 症状选择数量条形图")
                fig, ax = plt.subplots()
                ax.bar(["选择的症状"], [len(selected_symptoms)], color="skyblue")
                ax.set_ylabel("数量")
                ax.set_title("选择的症状数量")
                st.pyplot(fig)

                # 症状选择占比饼图
                st.write("#### 症状选择占比饼图")
                total_symptoms = len({symptom for disorder in knowledge_graph for symptom in disorder["symptom"]})
                fig, ax = plt.subplots()
                ax.pie(
                    [len(selected_symptoms), total_symptoms - len(selected_symptoms)],
                    labels=["选择的症状", "未选择的症状"],
                    autopct="%1.1f%%",
                    colors=["lightcoral", "lightgrey"],
                    startangle=90,
                )
                ax.set_title("症状选择占比")
                st.pyplot(fig)
            else:
                st.warning("根据选择的症状，未能匹配到已知的疾病。")
        else:
            st.warning("请先选择症状！")
    elif choice == "反馈":
        st.header("用户反馈")
        feedback = st.text_area("请留下您的宝贵意见：", "")
        if st.button("提交反馈"):
            st.success("感谢您的反馈！")
    elif choice == "隐私管理":
        st.header("隐私管理")
        st.markdown("""
                  **隐私声明：**
                  - 您的输入数据仅在本地会话中存储，不会上传或共享。
                  - 您可以随时清除所有会话数据。
                  """)
        if st.button("清除会话数据"):
            st.session_state.clear()
            st.success("所有会话数据已清除！")


if __name__ == "__main__":
    main()
