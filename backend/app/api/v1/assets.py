from flask import Blueprint, request
from ...services.asset_service import AssetService
from ...utils.logger import setup_logger
from ...utils.validators import validate_asset_create
from ...schemas.asset import AssetCreate, AssetUpdate, SshVerifyRequest
from ...utils.response import success_json, error_json, exception_handler, response_template

logger = setup_logger('assets_api')
assets_bp = Blueprint('assets', __name__)

@assets_bp.route('', methods=['GET'])
@exception_handler
def list_assets():
    """获取资产列表"""
    assets = AssetService.list_assets()
    return success_json([asset.dict() for asset in assets])

@assets_bp.route('', methods=['POST'])
@exception_handler
def create_asset():
    """创建新资产"""
    asset_data = AssetCreate(**request.json)
    asset = AssetService.create_asset(asset_data)
    if not asset:
        return error_json(2001, "创建资产失败")
    return response_template("created", data=asset.dict())

@assets_bp.route('/<int:asset_id>', methods=['PUT'])
@exception_handler
def update_asset(asset_id):
    """更新资产"""
    logger.debug(f"更新资产: {asset_id}, 原始请求数据: {request.json}")
    
    # 检查是否为本地资产
    from ...services.local_asset_service import LocalAssetService
    is_local = LocalAssetService.is_local_asset(asset_id)
    logger.info(f"资产 {asset_id} 是否为本地资产: {is_local}")
    
    # 如果是本地资产，确保is_local字段为True
    if is_local and 'is_local' not in request.json:
        request_data = dict(request.json)
        request_data['is_local'] = True
        logger.info(f"为本地资产 {asset_id} 添加is_local=True标志")
    else:
        request_data = request.json
        
    logger.debug(f"处理后的请求数据: {request_data}")
    update_data = AssetUpdate(**request_data)
    logger.debug(f"验证后的更新数据: {update_data}")
    
    asset = AssetService.update_asset(asset_id, update_data)
    if not asset:
        logger.warning(f"资产不存在或更新失败: {asset_id}")
        return response_template("not_found", code=2002, msg="资产不存在或更新失败")
        
    return response_template("updated", data=asset.dict())

@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
@exception_handler
def delete_asset(asset_id):
    """删除资产"""
    if AssetService.delete_asset(asset_id):
        return response_template("deleted")
    return error_json(2003, "删除资产失败")

@assets_bp.route('/<int:asset_id>/verify', methods=['POST'])
@exception_handler
def verify_capabilities(asset_id):
    """验证资产能力"""
    logger.info(f"开始验证资产 {asset_id} 的能力")
    results = AssetService.verify_capabilities(asset_id)
    logger.info(f"验证资产 {asset_id} 能力成功: {results}")
    return success_json(results)

@assets_bp.route('/verify-ssh', methods=['POST'])
@exception_handler
def verify_ssh_connection():
    """验证SSH连接"""
    # 验证请求数据
    data = SshVerifyRequest(**request.json)
    
    # 执行SSH连接验证
    AssetService.verify_ssh_connection(data.dict())
    
    return success_json(None, "SSH连接验证成功") 