from flask import Blueprint, request, jsonify
from ...services.asset_service import AssetService
from ...utils.logger import setup_logger
from ...utils.validators import validate_asset_create
from ...schemas.asset import AssetCreate, AssetUpdate

logger = setup_logger('assets_api')
assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/', methods=['GET'])
def list_assets():
    """获取资产列表"""
    assets = AssetService.list_assets()
    return jsonify(assets)

@assets_bp.route('/', methods=['POST'])
def create_asset():
    """创建新资产"""
    try:
        asset_data = AssetCreate(**request.json)
        asset = AssetService.create_asset(asset_data)
        if asset:
            return jsonify(asset)
        return jsonify({'error': '创建资产失败'}), 500
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@assets_bp.route('/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """更新资产"""
    try:
        update_data = AssetUpdate(**request.json)
        asset = AssetService.update_asset(asset_id, update_data)
        if asset:
            return jsonify(asset)
        return jsonify({'error': '资产不存在或更新失败'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """删除资产"""
    if AssetService.delete_asset(asset_id):
        return jsonify({'message': '资产已删除'})
    return jsonify({'error': '删除资产失败'}), 500

@assets_bp.route('/<int:asset_id>/verify', methods=['POST'])
def verify_capabilities(asset_id):
    """验证资产能力"""
    try:
        results = AssetService.verify_capabilities(asset_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 