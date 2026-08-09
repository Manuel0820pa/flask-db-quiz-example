
import os

import threading

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server


@pytest.fixture(scope="module")
def live_server_url(app):
    server = make_server("127.0.0.1", 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    if os.environ.get("CI"):
        # En GitHub Actions no hay pantalla; localmente se corre en modo
        # visual a proposito (el PDF pide evidencia de ejecucion visual).
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(5)
    yield drv
    drv.quit()


def test_e2e_home_page_lists_quiz(driver, live_server_url, fake_quiz):
    driver.get(live_server_url + "/")
    assert driver.title == "Quizzes"
    link = driver.find_element(By.LINK_TEXT, fake_quiz.title)
    assert link is not None


def test_e2e_open_quiz_shows_questions(driver, live_server_url, fake_quiz):
    driver.get(f"{live_server_url}/quizzes/{fake_quiz.id}")
    heading = driver.find_element(By.TAG_NAME, "h1")
    assert fake_quiz.title in heading.text
    assert "Who invented Python?" in driver.page_source


def test_e2e_submit_quiz_shows_score(driver, live_server_url, fake_quiz):
    driver.get(f"{live_server_url}/quizzes/{fake_quiz.id}")

    name_input = driver.find_element(By.CSS_SELECTOR, "input[name='player']")
    name_input.clear()
    name_input.send_keys("Selenium Tester")

    # Selecciona la primera opcion (correcta) de cada pregunta
    for question in fake_quiz.questions:
        first_choice = driver.find_element(
            By.CSS_SELECTOR, f"input[name='question{question.id}']"
        )
        first_choice.click()

    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
    submit_button.click()

    score_locator = (By.ID, "score")
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element(score_locator, "You scored")
    )
    score_text = driver.find_element(*score_locator).text
    assert "You scored" in score_text or "all right" in score_text


def test_e2e_high_scores_update_after_submit(driver, live_server_url, fake_quiz):
    driver.get(f"{live_server_url}/quizzes/{fake_quiz.id}")

    name_input = driver.find_element(By.CSS_SELECTOR, "input[name='player']")
    name_input.clear()
    name_input.send_keys("Selenium Ranker")

    for question in fake_quiz.questions:
        first_choice = driver.find_element(
            By.CSS_SELECTOR, f"input[name='question{question.id}']"
        )
        first_choice.click()

    submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
    submit_button.click()

    scores_locator = (By.ID, "scores")
    WebDriverWait(driver, 10).until(
        lambda d: "Selenium Ranker" in d.find_element(*scores_locator).text
    )
    scores_text = driver.find_element(*scores_locator).text
    assert "Selenium Ranker" in scores_text