"""Main GUI window with real-time Polymarket integration"""
import sys
import asyncio
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, 
    QListWidgetItem, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ..core.market import Market, PolymarketAPI
from ..core.arbitrage import ArbitrageDetector, ArbitrageOpportunity
from ..core.demo_mode import DemoMode
from ..utils.config import config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketFetchThread(QThread):
    """Background thread for fetching markets"""
    markets_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api: PolymarketAPI):
        super().__init__()
        self.api = api
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            markets = loop.run_until_complete(self.api.fetch_markets(limit=50))
            loop.close()
            self.markets_fetched.emit(markets)
        except Exception as e:
            self.error_occurred.emit(str(e))


class PriceUpdateThread(QThread):
    """Background thread for updating prices"""
    prices_updated = pyqtSignal(float, float)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api: PolymarketAPI, market: Market):
        super().__init__()
        self.api = api
        self.market = market
        self.running = False
    
    def run(self):
        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while self.running:
                # Fetch real prices from Polymarket
                yes_price, no_price = loop.run_until_complete(
                    self.api.get_market_prices(self.market)
                )
                self.prices_updated.emit(yes_price, no_price)
                
                # Update every 2 seconds to avoid rate limiting
                loop.run_until_complete(asyncio.sleep(2))
                
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            loop.close()
    
    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize Polymarket API
        self.api = PolymarketAPI()
        
        # Initialize components
        self.markets: List[Market] = []
        self.selected_market: Optional[Market] = None
        self.detector = ArbitrageDetector(
            min_profit=config.min_profit,
            trading_fee=config.trading_fee,
            gas_cost=config.gas_estimate
        )
        self.demo_mode = DemoMode(initial_balance=config.demo_balance)
        
        # Monitoring state
        self.monitoring = False
        self.price_thread: Optional[PriceUpdateThread] = None
        
        # Setup UI
        self.init_ui()
        
        # Auto-fetch markets on startup
        QTimer.singleShot(500, self.fetch_markets)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Polymarket Arbitrage Tool")
        self.setGeometry(100, 100, 1000, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title
        title = QLabel("⚡ Polymarket Arbitrage Bot")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Mode indicator
        mode_label = QLabel("🎮 DEMO MODE - Real prices, fake money")
        mode_label.setStyleSheet(
            "background-color: #e3f2fd; padding: 10px; "
            "border-radius: 5px; font-size: 12pt; color: #1976d2;"
        )
        mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(mode_label)
        
        # Market selection
        main_layout.addWidget(self.create_market_selection())
        
        # Price display
        main_layout.addWidget(self.create_price_display())
        
        # Controls
        main_layout.addLayout(self.create_controls())
        
        # Activity log
        main_layout.addWidget(self.create_log_display())
        
        # Status bar
        main_layout.addLayout(self.create_status_bar())
    
    def create_market_selection(self) -> QGroupBox:
        """Create market selection group"""
        group = QGroupBox("📊 Market Selection")
        layout = QVBoxLayout()
        
        # Search and refresh
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search markets...")
        self.search_input.textChanged.connect(self.on_search_changed)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.fetch_markets)
        
        search_layout.addWidget(self.search_input, 4)
        search_layout.addWidget(self.refresh_btn, 1)
        layout.addLayout(search_layout)
        
        # Market list
        self.market_list = QListWidget()
        self.market_list.itemClicked.connect(self.on_market_selected)
        layout.addWidget(self.market_list)
        
        group.setLayout(layout)
        return group
    
    def create_price_display(self) -> QGroupBox:
        """Create price display group"""
        group = QGroupBox("💰 Live Prices")
        layout = QVBoxLayout()
        
        # Market name
        self.market_name_label = QLabel("No market selected")
        self.market_name_label.setWordWrap(True)
        self.market_name_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        layout.addWidget(self.market_name_label)
        
        # Price display
        price_layout = QHBoxLayout()
        
        self.yes_price_label = QLabel("YES: --")
        self.yes_price_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; color: #2e7d32; "
            "background-color: #e8f5e9; padding: 15px; border-radius: 8px;"
        )
        
        self.no_price_label = QLabel("NO: --")
        self.no_price_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; color: #c62828; "
            "background-color: #ffebee; padding: 15px; border-radius: 8px;"
        )
        
        self.total_label = QLabel("Total: --")
        self.total_label.setStyleSheet(
            "font-size: 16pt; font-weight: bold; "
            "background-color: #f5f5f5; padding: 15px; border-radius: 8px;"
        )
        
        price_layout.addWidget(self.yes_price_label)
        price_layout.addWidget(self.no_price_label)
        price_layout.addWidget(self.total_label)
        layout.addLayout(price_layout)
        
        # Arbitrage alert
        self.arb_alert = QLabel("")
        layout.addWidget(self.arb_alert)
        
        group.setLayout(layout)
        return group
    
    def create_controls(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start Monitoring")
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #4caf50; color: white; "
            "padding: 10px; font-size: 12pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.start_btn.clicked.connect(self.start_monitoring)
        self.start_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; "
            "padding: 10px; font-size: 12pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #da190b; }"
        )
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        
        self.execute_btn = QPushButton("⚡ Execute Now")
        self.execute_btn.setStyleSheet(
            "QPushButton { background-color: #ff9800; color: white; "
            "padding: 10px; font-size: 12pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e68900; }"
        )
        self.execute_btn.clicked.connect(self.execute_once)
        self.execute_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn, 2)
        layout.addWidget(self.stop_btn, 1)
        layout.addWidget(self.execute_btn, 2)
        
        return layout
    
    def create_log_display(self) -> QGroupBox:
        """Create activity log"""
        group = QGroupBox("📋 Activity Log")
        layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(180)
        self.log_output.setStyleSheet("font-family: monospace; font-size: 10pt;")
        
        layout.addWidget(self.log_output)
        group.setLayout(layout)
        return group
    
    def create_status_bar(self) -> QHBoxLayout:
        """Create status bar"""
        layout = QHBoxLayout()
        
        self.balance_label = QLabel(f"💵 Balance: ${self.demo_mode.balance:.2f}")
        self.balance_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        
        self.profit_label = QLabel(f"📈 Profit: ${self.demo_mode.total_profit:.2f}")
        self.profit_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #2e7d32;")
        
        self.trades_label = QLabel(f"🔄 Trades: {self.demo_mode.num_trades}")
        self.trades_label.setStyleSheet("font-size: 11pt;")
        
        layout.addWidget(self.balance_label)
        layout.addWidget(self.profit_label)
        layout.addWidget(self.trades_label)
        layout.addStretch()
        
        return layout
    
    def fetch_markets(self):
        """Fetch markets from Polymarket"""
        self.log("🔄 Fetching markets from Polymarket...")
        self.refresh_btn.setEnabled(False)
        
        self.fetch_thread = MarketFetchThread(self.api)
        self.fetch_thread.markets_fetched.connect(self.on_markets_fetched)
        self.fetch_thread.error_occurred.connect(self.on_fetch_error)
        self.fetch_thread.start()
    
    def on_markets_fetched(self, markets: List[Market]):
        """Handle markets fetched"""
        self.markets = markets
        self.update_market_list(markets)
        self.log(f"✓ Loaded {len(markets)} active markets")
        self.refresh_btn.setEnabled(True)
    
    def on_fetch_error(self, error: str):
        """Handle fetch error"""
        self.log(f"❌ Error: {error}")
        self.refresh_btn.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Failed to fetch markets:\n{error}")
    
    def update_market_list(self, markets: List[Market]):
        """Update market list widget"""
        self.market_list.clear()
        for market in markets:
            item = QListWidgetItem(f"📊 {market.question}")
            item.setData(Qt.ItemDataRole.UserRole, market)
            self.market_list.addItem(item)
    
    def on_search_changed(self, text: str):
        """Handle search"""
        if not text:
            self.update_market_list(self.markets)
        else:
            filtered = [m for m in self.markets if text.lower() in m.question.lower()]
            self.update_market_list(filtered)
    
    def on_market_selected(self, item: QListWidgetItem):
        """Handle market selection"""
        self.selected_market = item.data(Qt.ItemDataRole.UserRole)
        self.market_name_label.setText(f"📊 {self.selected_market.question}")
        self.start_btn.setEnabled(True)
        self.log(f"✓ Selected: {self.selected_market.question}")
        
        # Reset display
        self.yes_price_label.setText("YES: --")
        self.no_price_label.setText("NO: --")
        self.total_label.setText("Total: --")
        self.arb_alert.setText("")
    
    def start_monitoring(self):
        """Start real-time price monitoring"""
        if not self.selected_market:
            return
        
        self.monitoring = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)
        
        self.log(f"▶ Monitoring started for: {self.selected_market.question}")
        self.log("📡 Fetching real-time prices from Polymarket...")
        
        # Start price update thread
        self.price_thread = PriceUpdateThread(self.api, self.selected_market)
        self.price_thread.prices_updated.connect(self.on_prices_updated)
        self.price_thread.error_occurred.connect(self.on_price_error)
        self.price_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        
        if self.price_thread:
            self.price_thread.stop()
            self.price_thread.wait()
            self.price_thread = None
        
        self.log("⏹ Stopped monitoring")
    
    def on_prices_updated(self, yes_price: float, no_price: float):
        """Handle real-time price updates"""
        if not self.monitoring:
            return
        
        try:
            # Validate price inputs
            if not isinstance(yes_price, (int, float)) or not isinstance(no_price, (int, float)):
                logger.warning(f"Invalid price types: YES={type(yes_price)}, NO={type(no_price)}")
                return
            
            if yes_price < 0 or yes_price > 1 or no_price < 0 or no_price > 1:
                logger.warning(f"Invalid price ranges: YES={yes_price}, NO={no_price}")
                return
            
            # Update display
            self.yes_price_label.setText(f"YES: ${yes_price:.4f}")
            self.no_price_label.setText(f"NO: ${no_price:.4f}")
            
            total = yes_price + no_price
            self.total_label.setText(f"Total: ${total:.4f}")
            
            # Color-code total based on arbitrage potential
            if total < 0.98:
                # Potential arbitrage - green
                self.total_label.setStyleSheet(
                    "font-size: 16pt; font-weight: bold; color: #2e7d32; "
                    "background-color: #e8f5e9; padding: 15px; border-radius: 8px;"
                )
            elif total > 1.02:
                # Expensive - red
                self.total_label.setStyleSheet(
                    "font-size: 16pt; font-weight: bold; color: #c62828; "
                    "background-color: #ffebee; padding: 15px; border-radius: 8px;"
                )
            else:
                # Normal - gray
                self.total_label.setStyleSheet(
                    "font-size: 16pt; font-weight: bold; "
                    "background-color: #f5f5f5; padding: 15px; border-radius: 8px;"
                )
            
            # Check for arbitrage
            if self.selected_market:
                try:
                    opp = self.detector.check_arbitrage(
                        self.selected_market.id,
                        self.selected_market.question,
                        yes_price,
                        no_price
                    )
                    
                    if opp:
                        # Show arbitrage alert
                        alert_text = (
                            f"🚨 ARBITRAGE OPPORTUNITY!\n"
                            f"💰 Profit: ${opp.estimated_profit:.4f} ({opp.profit_percentage:.2f}%)\n"
                            f"📊 Total Cost: ${total:.4f}"
                        )
                        self.arb_alert.setText(alert_text)
                        self.arb_alert.setStyleSheet(
                            "font-size: 13pt; font-weight: bold; color: #1b5e20; "
                            "background-color: #c8e6c9; padding: 15px; border-radius: 8px; "
                            "border: 2px solid #4caf50;"
                        )
                        
                        # Auto-execute if enabled
                        if config.auto_execute and opp.estimated_profit > 0.005:  # Only auto-execute if profit > $0.005
                            self.execute_arbitrage(opp)
                    else:
                        self.arb_alert.setText("")
                        
                except Exception as e:
                    logger.error(f"Error checking arbitrage: {e}")
                    self.arb_alert.setText("⚠️ Error checking arbitrage")
                    self.arb_alert.setStyleSheet(
                        "font-size: 12pt; color: #d32f2f; background-color: #ffebee; "
                        "padding: 10px; border-radius: 5px;"
                    )
                    
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            self.log(f"❌ Price update error: {e}")
    
    def on_price_error(self, error: str):
        """Handle price fetch error"""
        self.log(f"⚠️ Price update error: {error}")
    
    def execute_once(self):
        """Execute arbitrage manually"""
        if not self.selected_market:
            return
        
        # Get current prices
        yes_text = self.yes_price_label.text().split('$')[1] if '$' in self.yes_price_label.text() else None
        no_text = self.no_price_label.text().split('$')[1] if '$' in self.no_price_label.text() else None
        
        if not yes_text or not no_text:
            self.log("❌ No prices available")
            return
        
        try:
            yes_price = float(yes_text)
            no_price = float(no_text)
        except:
            self.log("❌ Invalid prices")
            return
        
        # Check for arbitrage
        opp = self.detector.check_arbitrage(
            self.selected_market.id,
            self.selected_market.question,
            yes_price,
            no_price
        )
        
        if opp:
            self.execute_arbitrage(opp)
        else:
            self.log("❌ No arbitrage opportunity at current prices")
    
    def execute_arbitrage(self, opp: ArbitrageOpportunity):
        """Execute arbitrage trade in demo mode"""
        try:
            # Execute demo trade
            trade = self.demo_mode.execute_arbitrage(
                market_name=opp.market_name,
                yes_price=opp.yes_price,
                no_price=opp.no_price,
                trading_fee=self.detector.trading_fee,
                gas_cost=self.detector.gas_cost
            )
            
            if trade is None:
                self.log("❌ Trade execution failed!")
                return
            
            # Log trade details
            self.log("=" * 50)
            self.log(f"⚡ ARBITRAGE EXECUTED")
            self.log(f"   Market: {opp.market_name[:50]}...")
            self.log(f"   YES: ${opp.yes_price:.4f} | NO: ${opp.no_price:.4f}")
            self.log(f"   💰 Profit: ${trade.profit:.4f}")
            self.log(f"   📊 Balance: ${self.demo_mode.balance:.2f}")
            self.log("=" * 50)
            
            # Update status
            self.update_status()
            
            # Clear alert
            self.arb_alert.setText("")
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            self.log(f"❌ Execution error: {e}")
            self.arb_alert.setText("❌ Execution failed")
            self.arb_alert.setStyleSheet(
                "font-size: 12pt; color: #d32f2f; background-color: #ffebee; "
                "padding: 10px; border-radius: 5px;"
            )
    
    def update_status(self):
        """Update status bar"""
        self.balance_label.setText(f"💵 Balance: ${self.demo_mode.balance:.2f}")
        self.profit_label.setText(f"📈 Profit: ${self.demo_mode.total_profit:.2f}")
        self.trades_label.setText(f"🔄 Trades: {self.demo_mode.num_trades}")
    
    def log(self, message: str):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.price_thread:
            self.price_thread.stop()
            self.price_thread.wait()
        
        # Close API session
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.api.close())
        loop.close()
        
        event.accept()


def run_gui():
    """Run the GUI application"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
