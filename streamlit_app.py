import streamlit as st
from PIL import Image
import base64
from io import BytesIO
import os
import zipfile
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="TestBot - QA Assistant",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 TestBot")
st.subheader("QA Team Assistant for Manual Test Cases, Test Plans & Selenium + Cucumber + JUnit 4 Automation")

# xAI Client (updated for 2026 models)
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": """👋 Welcome Buddy! I'm TestBot — your dedicated QA companion.

I can help your team with:
• Detailed **Manual Test Cases** (with steps, expected results, priority)
• Complete **Test Plan** documents
• Production-ready **Selenium + Cucumber + JUnit 4** automation (Java + Maven + Page Object Model)

**How to use:**
1. Upload UI screenshots (multiple supported)
2. Describe the feature/requirement
3. Or use Quick Actions on the sidebar

Grok-4.20 will analyze your UI and generate everything accurately."""}
    ]

if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []  # list of (filename, base64)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("Quick Start")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📋 Manual Test Cases", use_container_width=True):
            st.session_state.messages.append({"role": "user",
                                              "content": "Please generate detailed manual test cases for the uploaded UI and described feature."})
            st.rerun()
    with col_b:
        if st.button("📑 Test Plan", use_container_width=True):
            st.session_state.messages.append(
                {"role": "user", "content": "Create a complete professional Test Plan document."})
            st.rerun()

    if st.button("⚙️ Full Automation (Selenium + Cucumber + JUnit 4)", use_container_width=True):
        st.session_state.messages.append({"role": "user",
                                          "content": "Generate the complete Maven project with Selenium, Cucumber, JUnit 4, Page Objects, feature files, and test runner."})
        st.rerun()

    st.divider()
    st.caption("**Model**: grok-4.20-reasoning (best for code + reasoning)")
    st.caption("Vision support enabled for UI screenshots")

    if st.button("🗑️ Clear Everything & New Session", use_container_width=True, type="secondary"):
        st.session_state.messages = [{"role": "assistant",
                                      "content": "New session started. Please upload fresh UI screenshots or describe the new feature."}]
        st.session_state.uploaded_images = []
        st.rerun()

# ===================== CHAT DISPLAY =====================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "images" in msg:
            for img_info in msg["images"]:
                st.image(img_info["base64"], caption=img_info["filename"], use_column_width=True)

# ===================== INPUT =====================
user_input = st.chat_input("Describe the requirement (e.g., Login page with email, password, remember me)...")

uploaded_files = st.file_uploader(
    "Upload UI Screenshots (PNG/JPG)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="Grok will analyze the visible elements automatically"
)

# Process new uploads
if uploaded_files:
    new_images = []
    for file in uploaded_files:
        image = Image.open(file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        new_images.append({
            "filename": file.name,
            "base64": f"data:image/png;base64,{img_str}"
        })

        st.session_state.uploaded_images.append({
            "filename": file.name,
            "base64": img_str
        })

    # Add to chat
    with st.chat_message("user"):
        st.markdown("Uploaded UI screenshots:")
        for img in new_images:
            st.image(img["base64"], caption=img["filename"], use_column_width=True)

    st.session_state.messages.append({
        "role": "user",
        "content": f"Uploaded {len(new_images)} UI screenshot(s) for analysis.",
        "images": new_images
    })
    st.rerun()

# ===================== PROCESS USER INPUT =====================
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build messages for API
    api_messages = [{"role": "system", "content": """You are TestBot, an expert QA Automation Engineer.
You create high-quality artifacts for software testing teams.
When UI screenshots are provided, carefully analyze all visible elements (labels, fields, buttons, checkboxes, links, validation messages, etc.) and generate relevant tests.

Always respond professionally and structure output clearly.
For automation, generate a complete Maven project structure ready to run."""}]

    # Add history + images
    for m in st.session_state.messages:
        if m["role"] == "assistant":
            api_messages.append({"role": "assistant", "content": m["content"]})
        elif m["role"] == "user":
            content_parts = [{"type": "text", "text": m["content"]}]

            if "images" in m:
                for img in m["images"]:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": img["base64"], "detail": "high"}
                    })

            api_messages.append({"role": "user", "content": content_parts if len(content_parts) > 1 else m["content"]})

    # Call Grok
    with st.chat_message("assistant"):
        with st.spinner("Grok-4.20 is analyzing UI + generating QA artifacts..."):
            try:
                response = client.chat.completions.create(
                    model="grok-4.20-reasoning",  # Updated to current flagship
                    messages=api_messages,
                    temperature=0.6,
                    max_tokens=8000
                )
                bot_reply = response.choices[0].message.content.strip()

                st.markdown(bot_reply)

                st.session_state.messages.append({"role": "assistant", "content": bot_reply})

                # Auto-download buttons for common outputs
                if any(keyword in bot_reply.lower() for keyword in ["test case", "tc0", "manual test"]):
                    st.download_button(
                        "📥 Download Manual Test Cases (Markdown)",
                        bot_reply,
                        file_name=f"manual_test_cases_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown"
                    )

            except Exception as e:
                st.error(f"Error calling xAI API: {str(e)}")
                st.info("Check your XAI_API_KEY in .env and ensure it has sufficient credits.")

# ===================== FULL PROJECT ZIP EXPORT =====================
if st.button("📦 Export Complete Package (Test Plan + Test Cases + Full Maven Project)", type="primary",
             use_container_width=True):
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Summary
        summary = "TestBot Session Summary\nGenerated on: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n"
        for m in st.session_state.messages:
            summary += f"{m['role'].upper()}: {m.get('content', '')[:800]}...\n\n"
        zf.writestr("00_SESSION_SUMMARY.txt", summary)

        # Add last bot response as test artifacts
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            last_reply = st.session_state.messages[-1]["content"]
            zf.writestr("01_TEST_ARTIFACTS.md", last_reply)

        # Full Maven Project Structure (ready-to-use)
        base = "automation_project/"

        # pom.xml
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.qa</groupId>
    <artifactId>testbot-automation</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <cucumber.version>7.18.0</cucumber.version>
        <selenium.version>4.25.0</selenium.version>
        <junit.version>4.13.2</junit.version>
    </properties>

    <dependencies>
        <!-- Cucumber -->
        <dependency>
            <groupId>io.cucumber</groupId>
            <artifactId>cucumber-java</artifactId>
            <version>${cucumber.version}</version>
        </dependency>
        <dependency>
            <groupId>io.cucumber</groupId>
            <artifactId>cucumber-junit</artifactId>
            <version>${cucumber.version}</version>
        </dependency>
        <!-- Selenium -->
        <dependency>
            <groupId>org.seleniumhq.selenium</groupId>
            <artifactId>selenium-java</artifactId>
            <version>${selenium.version}</version>
        </dependency>
        <!-- JUnit -->
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>${junit.version}</version>
        </dependency>
        <!-- WebDriverManager -->
        <dependency>
            <groupId>io.github.bonigarcia</groupId>
            <artifactId>webdrivermanager</artifactId>
            <version>5.9.2</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.5.0</version>
                <configuration>
                    <includes>
                        <include>**/*Runner.java</include>
                    </includes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""
        zf.writestr(base + "pom.xml", pom_content)

        # Example Feature file
        feature = """Feature: Login Functionality
  As a registered user
  I want to login to the application
  So that I can access my account

  Scenario: Successful login with valid credentials
    Given user is on the login page
    When user enters valid email and password
    And clicks on the login button
    Then user should be redirected to the dashboard
"""
        zf.writestr(base + "src/test/resources/features/login.feature", feature)

        # Step Definitions skeleton
        steps = """package com.qa.stepdefinitions;

import io.cucumber.java.en.*;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import io.github.bonigarcia.wdm.WebDriverManager;

public class LoginSteps {
    WebDriver driver;

    @Given("user is on the login page")
    public void userOnLoginPage() {
        WebDriverManager.chromedriver().setup();
        driver = new ChromeDriver();
        driver.get("https://your-app-url.com/login");
    }

    @When("user enters valid email and password")
    public void enterCredentials() {
        // Implement using Page Object
    }

    @And("clicks on the login button")
    public void clickLogin() {
        // Implement
    }

    @Then("user should be redirected to the dashboard")
    public void verifyDashboard() {
        // Add assertion
        driver.quit();
    }
}
"""
        zf.writestr(base + "src/test/java/com/qa/stepdefinitions/LoginSteps.java", steps)

        # Test Runner
        runner = """package com.qa.runners;

import io.cucumber.junit.Cucumber;
import io.cucumber.junit.CucumberOptions;
import org.junit.runner.RunWith;

@RunWith(Cucumber.class)
@CucumberOptions(
    features = "src/test/resources/features",
    glue = "com.qa.stepdefinitions",
    plugin = {"pretty", "html:target/cucumber-report.html"},
    monochrome = true
)
public class TestRunner {
}
"""
        zf.writestr(base + "src/test/java/com/qa/runners/TestRunner.java", runner)

        # README
        readme = """# TestBot Generated Automation Project

## How to Run
1. mvn clean test
2. Or run TestRunner.java directly

Project uses:
- Selenium 4.25+
- Cucumber 7.18+
- JUnit 4
- Page Object Model (recommended)

Generated by TestBot on """ + datetime.now().strftime("%Y-%m-%d") + """
"""
        zf.writestr(base + "README.md", readme)

    zip_buffer.seek(0)

    st.success("✅ Full Maven project generated successfully!")
    st.download_button(
        label="⬇️ Download Complete ZIP Package",
        data=zip_buffer,
        file_name=f"TestBot_QA_Artifacts_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
        mime="application/zip",
        use_container_width=True
    )

st.caption("Powered by **xAI Grok-4.20-reasoning** • Vision enabled • Designed for your QA Team in Delhi")
