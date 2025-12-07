# Tax-Calculator-and-Stock-Tracker-
A Python-based desktop application that provides an integrated interface for tax calculation and stock price tracking. The application is built entirely using wxPython for the GUI and uses the yfinance library to fetch real-time stock market data. Graphs are displayed using Matplotlib, fully embedded within the GUI
# Tax Calculator and Stock Price Tracker (Python + wxPython)

## Overview
This project is a desktop-based Python application that combines:
1. A Tax Calculator with user-defined slabs and deductions.
2. A Stock Price Tracker that fetches real-time prices using the AlphaVantage API and displays graphs using Matplotlib.

The GUI is created entirely using wxPython, ensuring a clean, responsive, and user-friendly interface.

---

## Features
### 1. Login System
- Simple authentication using username and password stored in CSV.
- Credentials stored in dictionary form.

### 2. Tax Calculator
- Enter income and custom tax slabs.
- Add/update deductions.
- Automatic computation of taxable income and final tax.

### 3. Stock Tracker
- Enter stock ticker.
- Fetch real-time price.
- Embedded Matplotlib chart for daily time series.
- API: AlphaVantage

### 4. Deductions Manager
- Add, update, delete deductions.
- Stored persistently in CSV.

---

## Technologies Used
- Python 3.x  
- wxPython  
- Matplotlib  
- AlphaVantage API  
- CSV for persistence  

---

## Installation
