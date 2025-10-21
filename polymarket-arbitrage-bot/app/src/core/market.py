"""Market data fetching and real-time price monitoring"""
import asyncio
import aiohttp
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Market:
    """Represents a Polymarket market"""
    id: str
    question: str
    condition_id: str
    yes_token_id: str = ""
    no_token_id: str = ""
    yes_price: float = 0.0
    no_price: float = 0.0
    active: bool = True
    
    def __str__(self):
        return f"{self.question} (YES: ${self.yes_price:.4f}, NO: ${self.no_price:.4f})"


class PolymarketAPI:
    """Real-time Polymarket API integration"""
    
    def __init__(self):
        self.gamma_api = "https://gamma-api.polymarket.com"
        self.clob_api = "https://clob.polymarket.com"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            headers = {
                'User-Agent': 'Polymarket-Arbitrage-Bot/1.0.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                headers=headers,
                connector=connector
            )
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_markets(self, limit: int = 50) -> List[Market]:
        """Fetch active markets from Polymarket"""
        await self._ensure_session()
        
        try:
            url = f"{self.gamma_api}/markets"
            params = {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "archived": "false"
            }
            
            logger.info(f"Fetching {limit} markets from Polymarket...")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    logger.warning("Rate limited by Polymarket API, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    return await self.fetch_markets(limit)
                
                if response.status != 200:
                    logger.error(f"Failed to fetch markets: HTTP {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text[:200]}...")
                    return []
                
                try:
                    data = await response.json()
                except Exception as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    return []
                
                if not isinstance(data, list):
                    logger.error(f"Unexpected response format: {type(data)}")
                    return []
                
                markets = []
                
                for item in data[:limit]:
                    try:
                        # Validate required fields
                        if not isinstance(item, dict):
                            logger.warning(f"Invalid market item format: {type(item)}")
                            continue
                        
                        # Extract market data with validation
                        market_id = item.get('id', '')
                        if not market_id:
                            logger.warning("Market missing ID, skipping")
                            continue
                        
                        condition_id = item.get('condition_id', item.get('conditionId', ''))
                        question = item.get('question', 'Unknown Market')
                        
                        # Validate question length
                        if len(question) > 200:
                            question = question[:197] + "..."
                        
                        # Get token IDs from clobTokenIds (new API format)
                        clob_token_ids = item.get('clobTokenIds', [])
                        
                        # Handle case where clobTokenIds is a JSON string
                        if isinstance(clob_token_ids, str):
                            try:
                                import json
                                clob_token_ids = json.loads(clob_token_ids)
                            except (json.JSONDecodeError, ValueError):
                                clob_token_ids = []
                        
                        if isinstance(clob_token_ids, list) and len(clob_token_ids) >= 2:
                            yes_token = clob_token_ids[0] if len(clob_token_ids) > 0 else ''
                            no_token = clob_token_ids[1] if len(clob_token_ids) > 1 else ''
                        else:
                            # Fallback to old format
                            tokens = item.get('tokens', [])
                            if isinstance(tokens, list) and len(tokens) >= 2:
                                yes_token = tokens[0].get('token_id', '') if len(tokens) > 0 else ''
                                no_token = tokens[1].get('token_id', '') if len(tokens) > 1 else ''
                            else:
                                logger.warning(f"Market {market_id} missing proper token structure")
                                continue
                        
                        if not yes_token or not no_token:
                            logger.warning(f"Market {market_id} missing token IDs")
                            continue
                        
                        market = Market(
                            id=market_id,
                            question=question,
                            condition_id=condition_id,
                            yes_token_id=yes_token,
                            no_token_id=no_token,
                            active=item.get('active', True)
                        )
                        markets.append(market)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing market {item.get('id', 'unknown')}: {e}")
                        continue
                
                logger.info(f"[OK] Fetched {len(markets)} valid markets")
                return markets
                
        except asyncio.TimeoutError:
            logger.error("Timeout fetching markets from Polymarket")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching markets: {e}", exc_info=True)
            return []
    
    async def search_markets(self, query: str, limit: int = 20) -> List[Market]:
        """Search for markets by query string"""
        await self._ensure_session()
        
        try:
            url = f"{self.gamma_api}/markets"
            params = {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "archived": "false",
                "query": query.strip()
            }
            
            logger.info(f"Searching markets for: '{query}'")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    logger.warning("Rate limited by Polymarket API, retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    return await self.search_markets(query, limit)
                
                if response.status != 200:
                    logger.error(f"Failed to search markets: HTTP {response.status}")
                    return []
                
                try:
                    data = await response.json()
                except Exception as e:
                    logger.error(f"Failed to parse search JSON response: {e}")
                    return []
                
                if not isinstance(data, list):
                    logger.error(f"Unexpected search response format: {type(data)}")
                    return []
                
                markets = []
                
                for item in data[:limit]:
                    try:
                        # Validate required fields
                        if not isinstance(item, dict):
                            continue
                        
                        market_id = item.get('id', '')
                        if not market_id:
                            continue
                        
                        condition_id = item.get('condition_id', item.get('conditionId', ''))
                        question = item.get('question', 'Unknown Market')
                        
                        # Validate question length
                        if len(question) > 200:
                            question = question[:197] + "..."
                        
                        # Get token IDs
                        clob_token_ids = item.get('clobTokenIds', [])
                        
                        if isinstance(clob_token_ids, str):
                            try:
                                import json
                                clob_token_ids = json.loads(clob_token_ids)
                            except (json.JSONDecodeError, ValueError):
                                clob_token_ids = []
                        
                        if isinstance(clob_token_ids, list) and len(clob_token_ids) >= 2:
                            yes_token = clob_token_ids[0] if len(clob_token_ids) > 0 else ''
                            no_token = clob_token_ids[1] if len(clob_token_ids) > 1 else ''
                        else:
                            # Fallback to old format
                            tokens = item.get('tokens', [])
                            if isinstance(tokens, list) and len(tokens) >= 2:
                                yes_token = tokens[0].get('token_id', '') if len(tokens) > 0 else ''
                                no_token = tokens[1].get('token_id', '') if len(tokens) > 1 else ''
                            else:
                                continue
                        
                        if not yes_token or not no_token:
                            continue
                        
                        market = Market(
                            id=market_id,
                            question=question,
                            condition_id=condition_id,
                            yes_token_id=yes_token,
                            no_token_id=no_token,
                            active=item.get('active', True)
                        )
                        markets.append(market)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing search result {item.get('id', 'unknown')}: {e}")
                        continue
                
                logger.info(f"[OK] Found {len(markets)} markets matching '{query}'")
                return markets
                
        except asyncio.TimeoutError:
            logger.error("Timeout searching markets from Polymarket")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching markets: {e}", exc_info=True)
            return []
    
    async def get_live_prices(self, token_id: str) -> Optional[Dict[str, float]]:
        """Get real-time price for a specific token"""
        if not token_id:
            logger.warning("Empty token_id provided for price fetch")
            return None
            
        await self._ensure_session()
        
        try:
            url = f"{self.clob_api}/price"
            params = {"token_id": token_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    logger.debug(f"Rate limited for token {token_id}")
                    await asyncio.sleep(1)
                    return None
                
                if response.status == 404:
                    logger.debug(f"Token {token_id} not found")
                    return None
                
                if response.status != 200:
                    logger.debug(f"Price fetch failed for {token_id}: HTTP {response.status}")
                    return None
                
                try:
                    data = await response.json()
                except Exception as e:
                    logger.debug(f"Failed to parse price JSON for {token_id}: {e}")
                    return None
                
                if not isinstance(data, dict):
                    logger.debug(f"Invalid price data format for {token_id}")
                    return None
                
                # Extract and validate prices
                try:
                    mid_price = float(data.get('mid', data.get('price', 0.5)))
                    bid_price = float(data.get('bid', mid_price))
                    ask_price = float(data.get('ask', mid_price))
                    
                    # Validate price ranges (should be between 0 and 1 for prediction markets)
                    if not (0 <= mid_price <= 1) or not (0 <= bid_price <= 1) or not (0 <= ask_price <= 1):
                        logger.warning(f"Invalid price range for {token_id}: mid={mid_price}, bid={bid_price}, ask={ask_price}")
                        return None
                    
                    return {
                        'price': mid_price,
                        'bid': bid_price,
                        'ask': ask_price
                    }
                    
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing price values for {token_id}: {e}")
                    return None
                
        except asyncio.TimeoutError:
            logger.debug(f"Timeout fetching price for {token_id}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching price for {token_id}: {e}")
            return None
    
    async def get_market_prices(self, market: Market) -> tuple[float, float]:
        """Get current YES and NO prices for a market"""
        
        # Validate market has token IDs
        if not market.yes_token_id or not market.no_token_id:
            logger.warning(f"Market {market.id} missing token IDs")
            return 0.50, 0.50
        
        # Fetch prices concurrently for better performance
        yes_task = asyncio.create_task(self.get_live_prices(market.yes_token_id))
        no_task = asyncio.create_task(self.get_live_prices(market.no_token_id))
        
        try:
            yes_data, no_data = await asyncio.gather(yes_task, no_task, return_exceptions=True)
            
            # Handle exceptions from tasks
            if isinstance(yes_data, Exception):
                logger.debug(f"YES price fetch failed: {yes_data}")
                yes_data = None
            
            if isinstance(no_data, Exception):
                logger.debug(f"NO price fetch failed: {no_data}")
                no_data = None
            
            # Extract prices with fallbacks
            yes_price = yes_data['price'] if yes_data and isinstance(yes_data, dict) else 0.50
            no_price = no_data['price'] if no_data and isinstance(no_data, dict) else 0.50
            
            # Ensure prices are complementary (should sum close to 1.0 in efficient markets)
            total = yes_price + no_price
            if total > 1.2 or total < 0.8:
                logger.debug(f"Unusual price total for {market.id}: {total:.4f}")
            
            return yes_price, no_price
            
        except Exception as e:
            logger.error(f"Error fetching market prices for {market.id}: {e}")
            return 0.50, 0.50
    
    async def get_orderbook(self, token_id: str) -> Optional[Dict]:
        """Get full orderbook for a token"""
        await self._ensure_session()
        
        try:
            url = f"{self.clob_api}/book"
            params = {"token_id": token_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                return {
                    'bids': data.get('bids', []),
                    'asks': data.get('asks', [])
                }
                
        except Exception as e:
            logger.debug(f"Error fetching orderbook: {e}")
            return None
    
    async def place_order(
        self, 
        token_id: str, 
        side: str, 
        amount: float, 
        price: float
    ) -> Dict:
        """
        Simulate order placement (DEMO MODE)
        In production, this would use py-clob-client to place real orders
        """
        logger.info(f"[DEMO] Placing {side.upper()} order:")
        logger.info(f"[DEMO]   Token: {token_id}")
        logger.info(f"[DEMO]   Amount: ${amount:.4f}")
        logger.info(f"[DEMO]   Price: ${price:.4f}")
        
        # Simulate order success
        return {
            'success': True,
            'order_id': f"demo_{token_id[:8]}",
            'side': side,
            'amount': amount,
            'price': price,
            'status': 'filled'
        }
    
    async def execute_arbitrage_trade(
        self,
        market: Market,
        yes_price: float,
        no_price: float,
        amount: float = 1.0
    ) -> Dict:
        """
        Execute arbitrage trade (DEMO MODE)
        Buys YES and NO shares, simulates merge
        """
        logger.info(f"[DEMO] Executing arbitrage on: {market.question}")
        
        # Buy YES share
        yes_order = await self.place_order(
            market.yes_token_id,
            'buy',
            amount,
            yes_price
        )
        
        # Buy NO share
        no_order = await self.place_order(
            market.no_token_id,
            'buy',
            amount,
            no_price
        )
        
        # Simulate merge (in real mode, this would be a blockchain transaction)
        logger.info(f"[DEMO] Merging YES + NO positions...")
        logger.info(f"[DEMO] Received: ${amount:.4f}")
        
        return {
            'yes_order': yes_order,
            'no_order': no_order,
            'merge_amount': amount,
            'total_cost': yes_price + no_price,
            'profit': amount - (yes_price + no_price)
        }
