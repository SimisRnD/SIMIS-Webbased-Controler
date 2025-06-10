# Python Flask Project

This project is a Flask web application that includes image processing, QR code generation, serial communication, and computer vision capabilities.

## Prerequisites

- Python 3.7 or higher
- PowerShell (for Windows setup script)

## Quick Setup (Windows)

1. **Clone or download this project** to your local machine

2. **Navigate to the project directory** in PowerShell:
   ```powershell
   cd path/to/your/project
   ```

3. **Run the setup script**:
   ```powershell
   .\setup_environment.ps1
   ```
   
   If you encounter an execution policy error, first run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

The setup script will automatically:
- Create a virtual environment
- Activate it
- Upgrade pip
- Install all required dependencies

## Manual Setup (All Platforms)

If you prefer to set up manually or are using macOS/Linux:

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Upgrade pip**:
   ```bash
   python -m pip install --upgrade pip
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Ensure your virtual environment is activated**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. **Run your Flask application**:
   ```bash
   python app.py
   ```
   (Replace `app.py` with your main Flask file name)

## Project Dependencies

This project includes the following key libraries:
- **Flask**: Web framework for building the application
- **Pillow**: Image processing and manipulation
- **OpenCV**: Computer vision and image processing
- **QRCode**: QR code generation
- **PySerial**: Serial communication with hardware devices
- **PyProj**: Coordinate system transformations

## Troubleshooting

### Common Issues

**PowerShell Execution Policy Error**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python not found**:
- Ensure Python is installed and added to your system PATH
- Try using `python3` instead of `python`

**Virtual environment not activating**:
- Make sure you're in the correct project directory
- Check that the `venv` folder was created successfully

**Package installation errors**:
- Ensure pip is up to date: `python -m pip install --upgrade pip`
- Try installing packages individually if bulk installation fails

## Deactivating the Virtual Environment

When you're done working on the project, deactivate the virtual environment:
```bash
deactivate
```

## Additional Notes

- Always activate the virtual environment before working on the project
- The virtual environment keeps your project dependencies isolated from your system Python
- If you add new packages to your project, update the `requirements.txt` file:
  ```bash
  pip freeze > requirements.txt
  ```
