from flask import Blueprint, request, jsonify
from ...services.asset_service import AssetService
from ...utils.logger import setup_logger
from ...utils.validators import validate_asset_create
from ...schemas.asset import AssetCreate, AssetUpdate

logger = setup_logger('assets_api')
assets_bp = Blueprint('assets', __name__)

@assets_bp.route('', methods=['GET'])
def list_assets():
    """获取资产列表"""
    assets = AssetService.list_assets()
    return jsonify(assets)

@assets_bp.route('', methods=['POST'])
def create_asset():
    """创建新资产"""
    try:
        logger.debug(f"接收到创建资产请求: {request.json}")
        asset_data = AssetCreate(**request.json)
        asset = AssetService.create_asset(asset_data)
        if asset:
            logger.info(f"资产创建成功: {asset.dict()}")
            return jsonify(asset)
        logger.error("资产创建失败: 服务层返回None")
        return jsonify({'error': '创建资产失败'}), 500
    except ValueError as e:
        logger.warning(f"资产创建请求验证失败: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"资产创建请求处理异常: {str(e)}", exc_info=True)
        return jsonify({'error': '创建资产时发生错误'}), 500 