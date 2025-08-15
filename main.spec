# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集ddddocr相关数据文件
ddddocr_datas = collect_data_files('ddddocr')

a = Analysis(
    # 主要Python文件
    ['main.py'],

    # 指定搜索路径
    pathex=[
        '.',
        'src',
        'ddddocr'
    ],

    # 二进制文件（如果有特殊的.dll或.so文件）
    binaries=[],

    # 数据文件
    datas=[
        # ddddocr模型文件
        ('ddddocr/common.onnx', 'ddddocr/'),
        ('ddddocr/common_det.onnx', 'ddddocr/'),
        ('ddddocr/common_old.onnx', 'ddddocr/'),
        ('ddddocr/logo.png', 'ddddocr/'),
        ('ddddocr/README.md', 'ddddocr/'),
        ('ddddocr/requirements.txt', 'ddddocr/'),

        # src目录下的图片文件
        ('src/img.jpg', 'src/'),
        ('src/register/captcha_screenshot.png', 'src/register/'),
        ('src/register/img.jpg', 'src/register/'),
        ('src/util/verificationCode/captcha_screenshot.png', 'src/util/verificationCode/'),
    ] + ddddocr_datas,

    # 隐藏导入（PyInstaller可能无法自动检测的模块）
    hiddenimports=[
        # ddddocr相关
        'ddddocr',
        'ddddocr.api',
        'ddddocr.compat',
        'ddddocr.core',
        'ddddocr.models',
        'ddddocr.preprocessing',
        'ddddocr.utils',
        'onnxruntime',
        'cv2',
        'numpy',
        'pillow',
        'PIL',

        # 数据库相关
        'psycopg2',
        'pandas',
        'psutil',

        # 网络请求相关
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',

        # 时间处理
        'dateutil',
        'pytz',

        # XML处理
        'lxml',
        'lxml.etree',
        'lxml.html',

        # 其他可能用到的模块
        'selenium',
        'webdriver_manager',
        'bs4',
        'beautifulsoup4',

        # src模块
        'src.region.transporttation',
        'src.region.importtation',
        'src.intelligent.navigation',
        'src.decisionSys.order_monitor',
        'src.util.hw_util',
        'src.util.Agent',
        'src.util.verificationCode.ImageCode',
        'src.util.verificationCode.SlidingCode',
        'src.util.verificationCode.util.yunCode',
        'src.db.pgDatabase',
        'src.register.IM_platform',
        'src.register.jt_zineng',
        'src.register.management',
        'src.register.Decision_system',
        'src.AuthCode.mesmain',
    ],

    # Hook路径
    hookspath=[],

    # Hook配置
    hooksconfig={},

    # 运行时Hook
    runtime_hooks=[],

    # 排除的模块
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'distutils',
        'setuptools',
        'pip',
    ],

    noarchive=False,
    optimize=0,
)

# 过滤掉不需要的文件
def filter_binaries(binaries):
    """过滤二进制文件，移除不需要的文件"""
    filtered = []
    exclude_patterns = [
        'Qt5',  # 如果不使用Qt界面
        'matplotlib',  # 如果不使用matplotlib
        'IPython',  # 如果不使用IPython
    ]

    for binary in binaries:
        name = binary[0]
        exclude = False
        for pattern in exclude_patterns:
            if pattern.lower() in name.lower():
                exclude = True
                break
        if not exclude:
            filtered.append(binary)
    return filtered

# 应用过滤器
a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='中心监控脚本',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',  # 如果有图标文件，可以指定路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',  # 不压缩关键的运行时库
        'python3.dll',
        'python312.dll',
    ],
    name='main',
)
