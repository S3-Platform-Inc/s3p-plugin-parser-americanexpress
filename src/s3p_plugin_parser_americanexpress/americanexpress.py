import datetime
import time

from s3p_sdk.exceptions.parser import S3PPluginParserOutOfRestrictionException, S3PPluginParserFinish
from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument, S3PPlugin, S3PPluginRestrictions
from s3p_sdk.types.plugin_restrictions import FROM_DATE
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
import pytz
from random import uniform
import dateparser


class AMERICANEXPRESS(S3PParserBase):
    """
    A Parser payload that uses S3P Parser base class.
    """

    HOST = "https://www.americanexpress.com/en-us/newsroom/all-news.html"
    utc = pytz.UTC

    def __init__(self, refer: S3PRefer, plugin: S3PPlugin, restrictions: S3PPluginRestrictions, web_driver: WebDriver):
        super().__init__(refer, plugin, restrictions)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)

    def _parse(self, abstract=None):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -
        self._driver.get(self.HOST)  # Открыть страницу со списком RFC в браузере
        self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.stack-2')))

        while len(self._driver.find_elements(By.XPATH,
                                             '//span[contains(@class,\'btn\')]/span[contains(text(), \'Next\')]')) > 0:
            el_list = self._driver.find_elements(By.XPATH, '//div[contains(@class, \'card\')]')
            for el in el_list:
                article_link = el.find_element(By.CLASS_NAME, 'stack-2').find_element(By.TAG_NAME, 'a')
                web_link = article_link.get_attribute('href')
                title = article_link.text
                pub_date = dateparser.parse(el.find_element(By.CLASS_NAME, 'stack-3').find_element(By.TAG_NAME, 'p').text)
                self._driver.execute_script("window.open('');")
                self._driver.switch_to.window(self._driver.window_handles[1])
                time.sleep(uniform(0.1, 1.2))
                self._driver.get(web_link)
                self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.aem-container')))
                text_content = self._driver.find_element(By.XPATH, "//*[contains(@class, 'newsroom-container')]").text
                # print(web_link)
                # print(title)
                # print(pub_date)
                # print(text_content)
                # print('-' * 45)
                # if pub_date < self.date_begin:
                #     self.logger.info(f"Достигнута дата раньше {self.date_begin}. Завершение...")
                #     break

                other_data = None
                doc = S3PDocument(id=None,
                                  title=title,
                                  abstract=abstract,
                                  text=text_content,
                                  link=web_link,
                                  storage=None,
                                  other=other_data,
                                  published=pub_date,
                                  loaded=datetime.datetime.now())

                try:
                    self._find(doc)
                except S3PPluginParserOutOfRestrictionException as e:
                    if e.restriction == FROM_DATE:
                        self.logger.debug(f'Document is out of date range `{self._restriction.from_date}`')
                        raise S3PPluginParserFinish(self._plugin,
                                                    f'Document is out of date range `{self._restriction.from_date}`', e)

                self._driver.close()
                self._driver.switch_to.window(self._driver.window_handles[0])
            try:
                self._driver.execute_script('arguments[0].click()', self._driver.find_element(By.XPATH,
                                                                                              '//span[contains(@class,\'btn\')]/span[contains(text(), \'Next\')]'))
            except:
                # self.logger.info('Не найдено перехода на след. страницу. Завершение...')
                break
            self._wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, '.stack-2')))
            # print('=== NEW_PAGE ===')
            # print('=' * 90)

        # ---
        # ========================================
        ...
