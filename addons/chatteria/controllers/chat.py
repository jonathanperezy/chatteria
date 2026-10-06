# -*- coding: utf-8 -*-
import logging, os
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OdooAIChatController(http.Controller):

    @http.route('/chatteria/source.js', methods=['GET'], auth='public', csrf=False, type='http')
    def _chatteria_source(self, **kw):
        """ Call, clean and return a javascript text with the html and
        actions content from file /static/chatter/source
        """
        token = kw['token']
        remind_chat = kw.get('remind_chat', '1')
        current_path = os.path.dirname(os.path.realpath(__file__))
        source_file = os.path.abspath(os.path.join(current_path, '..', 'static', 'chatter', 'source.html'))
        odoo_url = request.env['ir.config_parameter'].sudo().get_base_url()

        with open(source_file, 'r') as source:
            chatter_html = source.read()
            chatter_html = chatter_html.replace('--source-token--', token)
            chatter_html = chatter_html.replace('--source-url--', odoo_url)
            chatter_html = chatter_html.replace('--remind--', remind_chat)
            minified = chatter_html.replace('\n', ' ').replace('  ', '')

            js_code = f"""
                document.addEventListener("DOMContentLoaded", function() {{
                    const new_div = document.createElement('div');
                    new_div.innerHTML = `{minified}`;
                    
                    document.body.appendChild(new_div);                    
                    new_div.querySelectorAll('script').forEach(original_script => {{
                        const new_script = document.createElement('script');
                        if (original_script.src) {{ new_script.src = original_script.src; }} 
                        else {{ new_script.textContent = original_script.textContent; }}
                        document.body.appendChild(new_script);
                        original_script.remove();
                    }});
                }});
            """
            return request.make_response(js_code, headers=[('Content-Type', 'text/javascript')])

    def _get_product_info(self, product_name: str) -> dict:
        """
        Internal helper method to search product price and stock availability in Odoo.
        """
        products = request.env['product.template'].sudo().search([
            ('name', 'ilike', product_name)
        ], limit=3)

        if not products:
            return {"status": "not_found", "message": f"No products found matching '{product_name}'."}

        results = []
        for product in products:
            results.append({
                "id": product.id,
                "name": product.name,
                "list_price": product.list_price,
                "qty_available": product.qty_available if hasattr(product, 'qty_available') else "N/A",
                "description": product.description_sale or "No description available."
            })
        
        return {"status": "success", "data": results}

    def _create_crm_lead(self, contact_name: str, contact_email: str = None, contact_phone: str = None, lead_description: str = None) -> dict:
        """
        Create a new lead/opportunity inside Odoo CRM module.

        Args:
            contact_name: The complete name of the interested customer.
            contact_email: The email address of the customer.
            contact_phone: The phone number of the customer.
            lead_description: Contextual notes or requirement details from the customer.
        """
        try:
            lead_values = {
                'name': f"Lead from AI Chat: {contact_name}",
                'contact_name': contact_name,
                'email_from': contact_email,
                'phone': contact_phone,
                'description': lead_description or "Customer interested via automated live chat.",
                'user_id': False, # Leave unassigned for general sales team assignment
            }
            
            # Write record natively using Odoo ORM with administrative privileges
            new_lead = request.env['crm.lead'].sudo().create(lead_values)
            
            return {
                "status": "success", 
                "message": "Lead registered successfully.", 
                "lead_id": new_lead.id
            }
        except Exception as e:
            _logger.error(f"CRM Lead creation failed via AI: {str(e)}")
            return {"status": "error", "message": f"Failed to record information inside CRM: {str(e)}"}

    def _check_api_access(self, **kwargs):
        """ Check if the api parameters are correct """
        if not kwargs.get('sender_id'):
            return None, {'status': 'error', 'message': 'Missing parameters: message and sender_id are required.'}

        received_token = kwargs.get('secure_token')
        uid = request.env['res.users.apikeys'].sudo()._check_credentials(
            scope='rpc', key=received_token
        )

        if not received_token or not uid:
            _logger.warning(f"Unauthorized JSON-RPC access attempt.")
            return None, {'status': 'error', 'message': 'Unauthorized access.'}

        request.update_env(user=uid)
        company = request.env.user.company_id

        if not company or not company.api_gemini_token:
            return None, {'status': 'error', 'message': 'Gemini API key is not configured.'}

        if company.allowed_url_ids:
            urls = company.allowed_url_ids.filtered(
                lambda url: url.available
            ).mapped('name')

            if request.httprequest.headers.get('Referer') not in urls:
                return None, {'status': 'error', 'message': 'Url unauthorized.'}

        return uid, {}

    @http.route('/api/v1/chat/load', type='jsonrpc', auth='public', methods=['POST'], cors='*', csrf=False)
    def proccess_ai_chat_load(self, **kwargs):
        """ When the page is loaded and remind is active this load all messages """
        uid, res = self._check_api_access(**kwargs)
        if res:
            return res

        sender_id = kwargs.get('sender_id')
        received_token = kwargs.get('secure_token')
        channel = kwargs.get('channel', 'web')
            
        # Fetch Past Conversation Context from DB
        past_records = request.env['ai.chat.history'].search([('sender_id', '=', sender_id)], limit=50)
        
        chat_contents = []
        for record in past_records:
            gemini_role = 'user' if record.role == 'user' else 'model'
            if record.role in ['system', 'tool']:
                continue
            chat_contents.append({
                'role': 'bot' if record.role == 'assistant' else record.role,
                'message': record.content
            })

        return {
            'status': 'success', 'data': chat_contents
        }

    # Restored to native type='json' for automatic JSON-RPC and CORS enforcement by Odoo core
    @http.route('/api/v1/chat', type='jsonrpc', auth='public', methods=['POST'], cors='*', csrf=False)
    def process_ai_chat(self, **kwargs):
        """
        Public secure JSON-RPC endpoint handling chat payloads linked to Google Gemini 3.8 API execution.
        """
        uid, res = self._check_api_access(**kwargs)
        if res:
            # error
            return res

        # Custom Security Token Validation
        received_token = kwargs.get('secure_token')
        user_message = kwargs.get('message')
        sender_id = kwargs.get('sender_id')
        channel = kwargs.get('channel', 'web')
        
        try:
            from google import genai
            from google.genai import types
            
            company = request.env.company
            
            client = genai.Client(api_key=company.api_gemini_token)

            # Save User Message into Odoo Database
            request.env['ai.chat.history'].sudo().create({
                'sender_id': sender_id,
                'role': 'user',
                'content': user_message,
                'channel': channel
            })

            # Fetch Past Conversation Context from DB
            past_records = request.env['ai.chat.history'].sudo().search([('sender_id', '=', sender_id)])
            
            gemini_contents = []
            for record in past_records:
                gemini_role = 'user' if record.role == 'user' else 'model'
                if record.role in ['system', 'tool']:
                    continue
                gemini_contents.append(
                    types.Content(role=gemini_role, parts=[types.Part.from_text(text=record.content)])
                )

            # Define System Instructions expanding role capability
            system_instruction = (
                "Eres el asistente inteligente de nuestra empresa, integrado directamente con Odoo v19. "
                "Debes responder de forma educada, servicial y SIEMPRE en idioma Español. "
                "Utiliza las herramientas disponibles para consultar información real antes de responder sobre existencias o precios. "
                "SI UN CLIENTE MUESTRA INTERÉS EN SER CONTACTADO O EN COMPRAR, debes pedir amablemente su Nombre completo, "
                "Correo electrónico y Teléfono. En cuanto te proporcione estos datos de contacto (mínimo el nombre), "
                "DEBES llamar inmediatamente a la herramienta '_create_crm_lead' para registrarlo en el CRM."
            )

            # Register both active Python methods into Gemini's tool matrix
            gemini_tools = [self._get_product_info, self._create_crm_lead]

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=gemini_tools,
                temperature=0.3
            )

            # Call Gemini API Execution with 503 retry framework
            response = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=gemini_contents,
                        config=config
                    )
                    break
                except Exception as api_err:
                    if "503" in str(api_err) and attempt < max_retries - 1:
                        time.sleep(1.5)
                        continue
                    raise api_err

            if not response:
                return {'status': 'error', 'message': 'Google API high demand.'}

            response_message = response.choices.message if hasattr(response, 'choices') else response

            # Process Function Calling router dynamically
            if response.function_calls:
                tool_responses = []
                for function_call in response.function_calls:
                    # Tool 1: Catalog Search Execution
                    if function_call.name == "_get_product_info":
                        args = function_call.args
                        product_name = args.get("product_name") or args.get("product", "")
                        tool_result = self._get_product_info(product_name=product_name)
                        
                        tool_responses.append(
                            types.Part.from_function_response(name=function_call.name, response=tool_result)
                        )
                    
                    # Tool 2: CRM Lead Insertion Execution
                    elif function_call.name == "_create_crm_lead":
                        args = function_call.args
                        tool_result = self._create_crm_lead(
                            contact_name=args.get("contact_name"),
                            contact_email=args.get("contact_email"),
                            contact_phone=args.get("contact_phone"),
                            lead_description=args.get("lead_description")
                        )
                        
                        tool_responses.append(
                            types.Part.from_function_response(name=function_call.name, response=tool_result)
                        )

                gemini_contents.append(response.candidates.content)
                gemini_contents.append(types.Content(role='user', parts=tool_responses))
                
                final_response = None
                for attempt in range(max_retries):
                    try:
                        final_response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=gemini_contents,
                            config=config
                        )
                        break
                    except Exception as api_err:
                        if "503" in str(api_err) and attempt < max_retries - 1:
                            time.sleep(1.5)
                            continue
                        raise api_err

                ai_response = final_response.text if final_response else "Error processing data."
            else:
                ai_response = response.text

            # Save Assistant Response back to Odoo DB
            request.env['ai.chat.history'].sudo().create({
                'sender_id': sender_id,
                'role': 'assistant',
                'content': ai_response,
                'channel': channel
            })

            return {
                'status': 'success',
                'response': ai_response
            }

        except Exception as e:
            _logger.error(f"Gemini JSON-RPC Chat Exception: {str(e)}")
