import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from main_content_extractor import MainContentExtractor
from playwright.async_api import Page

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.registry.service import Registry
from browser_use.controller.views import (
    ClickElementAction,
    DoneAction,
    ExtractPageContentAction,
    GoToUrlAction,
    InputTextAction,
    OpenTabAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
)
from browser_use.utils import time_execution_async, time_execution_sync

logger = logging.getLogger(__name__)

class Controller:
    def __init__(
        self,
        exclude_actions: list[str] = [],
    ):
        self.exclude_actions = exclude_actions
        self.registry = Registry(exclude_actions)
        self.action_log_path = Path("browser_actions.log")
        self._register_default_actions()
        
    async def _log_action_to_file(self, action_type: str, element_id: str = None, success: bool = True, error: str = None):
        """Log action details to persistent file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action_type,
            "element_id": element_id,
            "success": success,
            "error": error
        }
        try:
            with open(self.action_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write action log: {str(e)}")

    def _register_default_actions(self):
        """Register all default browser actions using the Registry's action decorator"""
        
        # Basic Navigation Actions
        @self.registry.action('Open url in new tab', param_model=OpenTabAction, requires_browser=True)
        async def open_tab(params: OpenTabAction, browser: BrowserContext):
            await browser.create_new_tab(params.url)
            msg = f'🔗  Opened new tab with {params.url}'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        @self.registry.action('Search Google in the current tab', param_model=SearchGoogleAction, requires_browser=True)
        async def search_google(params: SearchGoogleAction, browser: BrowserContext):
            page = await browser.get_current_page()
            await page.goto(f'https://www.google.com/search?q={params.query}&udm=14')
            await page.wait_for_load_state()
            msg = f'🔍  Searched for "{params.query}" in Google'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        @self.registry.action('Navigate to URL in the current tab', param_model=GoToUrlAction, requires_browser=True)
        async def go_to_url(params: GoToUrlAction, browser: BrowserContext):
            page = await browser.get_current_page()
            await page.goto(params.url)
            await page.wait_for_load_state()
            msg = f'🔗  Navigated to {params.url}'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        @self.registry.action('Go back', requires_browser=True)
        async def go_back(browser: BrowserContext):
            await browser.go_back()
            msg = '🔙  Navigated back'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)

        # Element Interaction Actions
        @self.registry.action('Click element', param_model=ClickElementAction, requires_browser=True)
        async def click_element(params: ClickElementAction, browser: BrowserContext):
            session = await browser.get_session()
            state = session.cached_state

            if params.index not in state.selector_map:
                raise Exception(f'Element with index {params.index} does not exist - retry or use alternative actions')

            element_node = state.selector_map[params.index]
            initial_pages = len(session.context.pages)
            html_id = element_node.attributes.get('id', None)

            # if element has file uploader then dont click
            if await browser.is_file_uploader(element_node):
                msg = f'Index {params.index} - has an element which opens file upload dialog. To upload files please use a specific function to upload files '
                logger.info(msg)
                await self._log_action_to_file("click", html_id, False, "File upload element")
                return ActionResult(extracted_content=msg, include_in_memory=True)

            try:
                await browser._click_element_node(element_node)
                msg = f'🖱️  Clicked button with index {params.index}: {element_node.get_all_text_till_next_clickable_element(max_depth=2)}'
                logger.info(msg)
                logger.debug(f'Element xpath: {element_node.xpath}')
                if html_id:
                    logger.debug(f'Element HTML id: {html_id}')
                    await self._log_action_to_file("click", html_id)
                
                if len(session.context.pages) > initial_pages:
                    new_tab_msg = 'New tab opened - switching to it'
                    msg += f' - {new_tab_msg}'
                    logger.info(new_tab_msg)
                    await browser.switch_to_tab(-1)
                
                return ActionResult(
                    extracted_content=msg,
                    include_in_memory=True,
                    html_id=html_id
                )
            except Exception as e:
                error_msg = str(e)
                logger.warning(f'Element not clickable with index {params.index} - most likely the page changed')
                if html_id:
                    logger.debug(f'Failed click had element HTML id: {html_id}')
                    await self._log_action_to_file("click", html_id, False, error_msg)
                return ActionResult(error=error_msg, html_id=html_id)

        @self.registry.action(
            'Input text into a input interactive element',
            param_model=InputTextAction,
            requires_browser=True,
        )
        async def input_text(params: InputTextAction, browser: BrowserContext):
            session = await browser.get_session()
            state = session.cached_state

            if params.index not in state.selector_map:
                raise Exception(f'Element index {params.index} does not exist - retry or use alternative actions')

            element_node = state.selector_map[params.index]
            html_id = element_node.attributes.get('id', None)
            
            try:
                await browser._input_text_element_node(element_node, params.text)
                msg = f'⌨️  Input "{params.text}" into index {params.index}'
                logger.info(msg)
                logger.debug(f'Element xpath: {element_node.xpath}')
                if html_id:
                    logger.debug(f'Input element HTML id: {html_id}')
                    await self._log_action_to_file("input", html_id)
                return ActionResult(extracted_content=msg, include_in_memory=True, html_id=html_id)
            except Exception as e:
                error_msg = str(e)
                if html_id:
                    await self._log_action_to_file("input", html_id, False, error_msg)
                return ActionResult(error=error_msg, html_id=html_id)

        # [Rest of the action implementations...]

    @time_execution_async('--multi-act')
    async def multi_act(self, actions: list[ActionModel], browser_context: BrowserContext, check_for_new_elements: bool = True) -> list[ActionResult]:
        """Execute multiple actions"""
        results = []
        session = await browser_context.get_session()
        cached_selector_map = session.cached_state.selector_map
        cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())
        await browser_context.remove_highlights()

        for i, action in enumerate(actions):
            if action.get_index() is not None and i != 0:
                new_state = await browser_context.get_state()
                new_path_hashes = set(e.hash.branch_path_hash for e in new_state.selector_map.values())
                if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
                    break

            results.append(await self.act(action, browser_context))
            if results[-1].is_done or results[-1].error or i == len(actions) - 1:
                break
            await asyncio.sleep(browser_context.config.wait_between_actions)

        return results

    @time_execution_sync('--act')
    async def act(self, action: ActionModel, browser_context: BrowserContext) -> ActionResult:
        """Execute an action"""
        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    result = await self.registry.execute_action(action_name, params, browser=browser_context)
                    html_id = getattr(result, 'html_id', None)
                    if html_id:
                        await self._log_action_to_file(action_name, html_id, result.error is None, result.error)
                    
                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    
            return ActionResult()
        except Exception as e:
            raise e
