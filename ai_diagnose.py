import streamlit as st
import json
from matplotlib import rcParams
from neo4j import GraphDatabase
import time
import io

rcParams['font.sans-serif'] = ['SimHei']  # 正常显示为中文标签
rcParams['axes.unicode_minus'] = False  # 防止负号显示为方块

# 配置 Neo4j 连接
URI = "neo4j://localhost:7687"  # 替换为你的 Neo4j 实例地址
USERNAME = "neo4j"  # 替换为你的用户名
PASSWORD = "20020000"  # 替换为你的密码
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


# 从 Neo4j 获取知识图谱数据
def fetch_graph_data(query):
    with driver.session() as session:
        result = session.run(query)
        nodes = set()
        edges = []
        for record in result:
            n = record["n"]
            m = record["m"]
            r = record["r"]
            nodes.add((n.element_id, n["name"]))
            nodes.add((m.element_id, m["name"]))
            edges.append((n.element_id, m.element_id, r.type))
        return list(nodes), edges


# 构建 HTML 可视化
def create_vis_html(nodes, edges):
    graph_data = {
        "nodes": [{"id": node[0], "label": node[1]} for node in nodes],
        "edges": [{"from": edge[0], "to": edge[1], "label": edge[2]} for edge in edges],
    }
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    </head>
    <body>
    <div id="network" style="width: 100%; height: 600px;"></div>
    <script>
      var nodes = new vis.DataSet({json.dumps(graph_data['nodes'])});
      var edges = new vis.DataSet({json.dumps(graph_data['edges'])});
      var container = document.getElementById('network');
      var data = {{ nodes: nodes, edges: edges }};
      var options = {{
        nodes: {{
          shape: 'dot',
          size: 15,
          font: {{ size: 14, color: '#000' }},
          borderWidth: 2
        }},
        edges: {{
          width: 2,
          font: {{ size: 12, align: 'middle' }},
          arrows: {{ to: {{ enabled: true, scaleFactor: 0.5 }} }},
          color: {{ color: '#848484', highlight: '#848484', hover: '#848484' }},
          smooth: {{ type: 'dynamic' }}
        }},
        physics: {{
          stabilization: false,
          barnesHut: {{
            gravitationalConstant: -8000,
            centralGravity: 0.3,
            springLength: 95,
            springConstant: 0.04
          }}
        }}
      }};
      var network = new vis.Network(container, data, options);
    </script>
    </body>
    </html>
    """


# 整合到诊断结果模块
def diagnosis_results_module(knowledge_graph):
    st.header("诊断结果")
    if "symptoms" in st.session_state and st.session_state["symptoms"]:
        selected_symptoms = st.session_state["symptoms"]
        diagnoses = get_diagnosis(selected_symptoms, knowledge_graph)

        if diagnoses:
            st.write("以下是根据您选择的症状生成的可能患有的疾病：")
            for diag in diagnoses:
                st.markdown(f"### {diag['疾病']}")
                st.markdown(f"**疾病描述：** {diag['疾病描述']}")
                st.markdown(f"**诊断标准：** {diag['诊断标准']}")
                st.markdown(f"**治疗建议：** {diag['治疗建议']}")

            # 动态展示知识图谱
            st.subheader("关联知识图谱")
            query = f"""
            MATCH (n)-[r]->(m)
            WHERE n.name IN {json.dumps([diag['疾病'] for diag in diagnoses])}
            RETURN n, r, m
            """
            nodes, edges = fetch_graph_data(query)
            vis_html = create_vis_html(nodes, edges)
            st.components.v1.html(vis_html, height=600)

        else:
            st.warning("根据选择的症状，未能匹配到已知的疾病。")
    else:
        st.warning("请先选择症状！")

    return diagnoses


# 安全模块的用户验证功能
def authenticate_user(username, password):
    # 简单的用户名和密码验证 (仅供示例，可替换为更安全的认证机制)
    user_credentials = {"shuimianjibing": "123456"}
    return user_credentials.get(username) == password


# 添加主安全模块
def security_module():
    st.title("安全模块")
    st.markdown("本模块用于确保系统的安全和数据隐私。")

    # 用户登录
    st.subheader("用户登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        if authenticate_user(username, password):
            st.success("登录成功！欢迎使用疾病诊断系统。")
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
        else:
            st.error("用户名或密码错误，请重试。")

    # 登录成功后显示额外功能
    if "authenticated" in st.session_state and st.session_state["authenticated"]:
        st.markdown(f"**当前用户：** {st.session_state['username']}")
        st.markdown("### 安全功能")

        # 数据清理功能
        if st.button("清除会话数据"):
            st.session_state.clear()
            st.success("所有会话数据已清除！")
            st.experimental_set_query_params()

        # 提示用户继续操作
        st.info("您已通过身份验证，可返回导航栏使用其他功能。")


# 添加测试模块
def test_module(knowledge_graph):
    st.title("测试模块")
    st.markdown("本模块用于测试系统的功能和知识图谱的准确性。")

    # 获取所有症状
    all_symptoms = set()
    for disorder in knowledge_graph:
        all_symptoms.update(disorder["symptom"])

    # 模拟输入
    st.subheader("症状输入模拟")
    test_symptoms = st.multiselect("选择测试症状：", list(all_symptoms))

    if st.button("运行测试"):
        if test_symptoms:
            # 获取诊断结果
            diagnoses = get_diagnosis(test_symptoms, knowledge_graph)
            if diagnoses:
                st.write("以下是根据测试症状生成的诊断结果：")
                for diag in diagnoses:
                    st.markdown(f"### {diag['疾病']}")
                    st.markdown(f"**疾病描述：** {diag['疾病描述']}")
                    st.markdown(f"**诊断标准：** {diag['诊断标准']}")
                    st.markdown(f"**治疗建议：** {diag['治疗建议']}")
            else:
                st.warning("未匹配到任何疾病。")
        else:
            st.warning("请选择至少一个症状以运行测试。")

    # 可视化知识图谱内容
    st.subheader("知识图谱内容分析")
    disorder_counts = len(knowledge_graph)
    symptom_counts = len(all_symptoms)
    st.markdown(f"- **疾病数量：** {disorder_counts}")
    st.markdown(f"- **独立症状数量：** {symptom_counts}")

    # 提供诊断的覆盖率
    st.subheader("诊断覆盖率测试")
    st.markdown("通过测试输入症状集合的匹配程度，计算诊断覆盖率。")
    matched_disorders = sum(
        1 for disorder in knowledge_graph if any(symptom in test_symptoms for symptom in disorder["symptom"])
    )
    coverage_rate = (matched_disorders / disorder_counts) * 100 if disorder_counts else 0
    st.markdown(f"- **覆盖的疾病数量：** {matched_disorders}")
    st.markdown(f"- **覆盖率：** {coverage_rate:.2f}%")

    if coverage_rate < 50:
        st.warning("诊断覆盖率较低，测试症状较少。")
    else:
        st.success("诊断覆盖率较高，测试症状较多。")


# 加载知识图谱函数
def load_knowledge_graph(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 根据症状获取诊断
def get_diagnosis(symptoms, knowledge_graph):
    possible_diagnoses = []

    # 遍历每个睡眠障碍（每个元素是一个字典）
    for disorder in knowledge_graph:
        # 判断症状是否至少匹配一个
        if any(symptom in disorder["symptom"] for symptom in symptoms):
            possible_diagnoses.append({
                "id": disorder["_id"],  # 获取疾病ID
                "疾病": disorder["name"],  # 获取疾病名称
                "疾病描述": disorder["desc"],  # 获取疾病描述
                "诊断标准": disorder["diag_criteria"],  # 获取诊断标准
                "治疗建议": disorder["cure_way"],  # 获取治疗建议
            })

    return possible_diagnoses


def modify_probability(data, step, target_ids):
    """
      根据多个target_ids修改数据中的probability字段
      :param data: JSON数据
      :param target_ids: 目标_id的列表
      :return: 修改后的数据
    """
    for item in data:
        if item.get('_id') in target_ids:  # 如果 _id 在目标列表中
            # 获取当前的 probability 字段
            if 'probability' in item:
                # 将概率值从字符串转换为数字并加 1%
                updated_probabilities = []
                for prob in item['probability']:
                    if step == "满意":
                        try:
                            prob_value = float(prob.replace('%', ''))  # 去掉百分号并转为浮动数值
                            numerator = prob_value  # 分子是百分数的值
                            denominator = 100  # 默认分母为100

                            # 分子分母同时加1
                            new_numerator = numerator + 1
                            new_denominator = denominator + 1

                            # 转换回百分数形式
                            new_prob = (new_numerator / new_denominator) * 100  # 计算百分数
                            updated_probabilities.append(f"{new_prob:.1f}%")  # 保留一位小数并加回百分号
                        except ValueError:
                            updated_probabilities.append(prob)  # 如果转换失败，保留原值
                    elif step == "不满意":
                        try:
                            prob_value = float(prob.replace('%', ''))  # 去掉百分号并转为浮动数值
                            numerator = prob_value  # 分子是百分数的值
                            denominator = 100  # 默认分母为100

                            # 分子分母同时加1
                            new_numerator = numerator - 1
                            new_denominator = denominator - 1

                            # 转换回百分数形式
                            new_prob = (new_numerator / new_denominator) * 100  # 计算百分数
                            updated_probabilities.append(f"{new_prob:.1f}%")  # 保留一位小数并加回百分号
                        except ValueError:
                            updated_probabilities.append(prob)  # 如果转换失败，保留原值
                    else:
                        updated_probabilities.append(prob)  # 如果转换失败，保留原值

                item['probability'] = updated_probabilities
    return data


# 主函数
def main():
    if "feedback_work" not in st.session_state:
        st.session_state["feedback_work"] = 0
    st.set_page_config(page_title="疾病诊断系统", layout="wide")

    # 加载知识图谱
    file_path = "sleep_konwledge_graph.json"
    # file_path = r"sleep_konwledge_graph.json"
    knowledge_graph = load_knowledge_graph(file_path)

    st.sidebar.markdown('<div style="font-size: 30px; font-weight: bold;">导航菜单</div>', unsafe_allow_html=True)
    # 使用 HTML 设置更大的字体
    tab_options = ["安全模块", "首页", "症状选择", "诊断结果", "测试模块", "反馈", "隐私管理"]

    choice = st.sidebar.radio("选择页面：", tab_options)

    if choice == "安全模块":
        security_module()
    elif "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.warning("请先通过 [安全模块] 登录后访问本系统其他功能。")

    elif choice == "测试模块":
        test_module(knowledge_graph)

    elif choice == "首页":
        st.title("欢迎使用疾病诊断系统")
        st.markdown("""
        **功能简介：**
        - 根据症状选择进行疾病诊断。
        - 提供诊断结果及治疗建议。
        - 支持数据可视化及用户反馈。
        """)
        st.info("隐私声明：本系统仅在会话中保存您的数据，所有输入均不会上传到服务器或外部存储。")

        st.subheader("请按照以下步骤在左侧边框中逐步操作：")
        # 第一步：选择症状
        step = st.radio("  ", ["选择症状", "确认症状", "查看结果"])


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
            st.success("症状已保存！即将跳转到诊断结果页面...")
            st.session_state["go_to_diagnosis"] = True  # 标记跳转
            st.session_state["feedback_work"] = 1
            time.sleep(1)  # 暂停 1 秒
            st.rerun()  # 强制重新运行，跳转到诊断结果页面

        # 在 main 函数的部分中检查是否需要跳转
        if "go_to_diagnosis" in st.session_state and st.session_state["go_to_diagnosis"]:
            # 将标记置为 False，以避免多次跳转
            st.session_state["go_to_diagnosis"] = False
            choice = "诊断结果"  # 设置跳转目标为诊断结果页面

        # 跳转到诊断结果页面
        if choice == "诊断结果":
            diagnosis_results_module(knowledge_graph)


    elif choice == "诊断结果":
        diagnosis_results_module(knowledge_graph)


    elif choice == "反馈":

        if st.session_state["feedback_work"] != 0:
            st.header("用户反馈")
            feedback = st.text_area("请留下您的宝贵意见：", "")
            step = st.radio("您对本次诊断满意吗？", [" ", "不确定", "满意", "不满意"])
            # 处理 probability 字段
            if "symptoms" in st.session_state and st.session_state["symptoms"]:
                selected_symptoms = st.session_state["symptoms"]
                possible_diagnoses = get_diagnosis(selected_symptoms, knowledge_graph)

            target_ids = [diag["id"] for diag in possible_diagnoses]
            updated_data = modify_probability(knowledge_graph, step, target_ids)

            # 将修改后的数据转为 JSON 字符串
            json_data = json.dumps(updated_data, ensure_ascii=False, indent=4)

            # 使用 StringIO 将 JSON 数据转为类文件对象
            json_buffer = io.StringIO(json_data)
            if step != " ":
                # 创建文件的下载链接
                st.download_button(
                    label="下载修改后的 JSON 文件",
                    data=json_buffer.getvalue(),
                    file_name="data_modified.json",
                    mime="application/json"
                )
        else:
            st.markdown("""
                              -请先进行症状选择与诊断结果获取
                              """)


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
