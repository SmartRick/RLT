from flask import Blueprint, request, jsonify
from ...services.asset_service import AssetService
from ...utils.logger import setup_logger

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
    asset = AssetService.create_asset(request.json)
    if asset:
        return jsonify(asset)
    return jsonify({'error': '创建资产失败'}), 500

@assets_bp.route('/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """更新资产"""
    asset = AssetService.update_asset(asset_id, request.json)
    if asset:
        return jsonify(asset)
    return jsonify({'error': '资产不存在或更新失败'}), 404

@assets_bp.route('/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """删除资产"""
    if AssetService.delete_asset(asset_id):
        return jsonify({'message': '资产已删除'})
    return jsonify({'error': '删除资产失败'}), 500

@assets_bp.route('/<asset_id>/upload', methods=['POST'])
def upload_files(asset_id):
    """上传资产文件"""
    if 'files' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
        
    files = request.files.getlist('files')
    result = AssetService.upload_files(asset_id, files)
    
    if result:
        return jsonify({'message': '文件上传成功'})
    return jsonify({'error': '文件上传失败'}), 500 