import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, BlockchainBlock, EncryptedAsset
from crypto_utils import Blockchain, Block, db_encrypt, db_decrypt

blockchain_bp = Blueprint('blockchain', __name__)

# In-memory blockchain instance
_blockchain = None


def get_blockchain():
    """Dapatkan atau buat instance blockchain dari database"""
    global _blockchain
    if _blockchain is None:
        _blockchain = Blockchain()

        # Load existing blocks from database
        blocks_db = BlockchainBlock.query.order_by(BlockchainBlock.index).all()
        if blocks_db:
            for block_db in blocks_db:
                block = Block(
                    index=block_db.index,
                    data=block_db.data,
                    previous_hash=block_db.previous_hash,
                    timestamp=block_db.timestamp
                )
                block.nonce = block_db.nonce
                block.hash = block_db.hash
                _blockchain.chain.append(block)

    return _blockchain


def save_block_to_db(block):
    """Simpan blok ke database"""
    block_db = BlockchainBlock(
        index=block.index,
        timestamp=block.timestamp,
        data=block.data if isinstance(block.data, str) else json.dumps(block.data),
        previous_hash=block.previous_hash,
        hash=block.hash,
        nonce=block.nonce
    )
    db.session.add(block_db)
    db.session.commit()
    return block_db


@blockchain_bp.route('/blockchain')
@login_required
def view_blockchain():
    """Lihat semua blok dalam blockchain"""
    blockchain = get_blockchain()
    blocks = []
    for block in blockchain.chain:
        blocks.append({
            'index': block.index,
            'timestamp': block.timestamp,
            'data': block.data,
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'nonce': block.nonce
        })

    is_valid = blockchain.is_chain_valid() if len(blockchain.chain) > 1 else True
    return render_template('blockchain.html', blocks=blocks, is_valid=is_valid)


@blockchain_bp.route('/blockchain/add-asset', methods=['POST'])
@login_required
def add_asset():
    """Tambah aset baru ke blockchain"""
    asset_name = request.form.get('asset_name', '').strip()
    asset_data = request.form.get('asset_data', '').strip()

    if not asset_name or not asset_data:
        flash('Nama aset dan data aset harus diisi.', 'danger')
        return redirect(url_for('blockchain.view_blockchain'))

    try:
        blockchain = get_blockchain()

        # Prepare block data
        block_data = json.dumps({
            'user_id': current_user.id,
            'username': current_user.username,
            'asset_name': asset_name,
            'action': 'CREATE_ASSET'
        })

        # Check if genesis block needs to be saved
        initial_len = len(blockchain.chain)

        # Add block to blockchain
        new_block = blockchain.add_block(block_data)

        # Save genesis block if it was just created
        if initial_len == 0 and len(blockchain.chain) > 1:
            save_block_to_db(blockchain.chain[0])  # Genesis block

        # Save new block to database
        save_block_to_db(new_block)

        # Encrypt and save asset data
        encrypted_asset_data = db_encrypt(asset_data)
        asset = EncryptedAsset(
            user_id=current_user.id,
            asset_name=asset_name,
            asset_data_encrypted=encrypted_asset_data,
            block_index=new_block.index
        )
        db.session.add(asset)
        db.session.commit()

        flash(f'Aset "{asset_name}" berhasil ditambahkan ke blockchain (Block #{new_block.index})!', 'success')

    except Exception as e:
        flash(f'Gagal menambah aset: {str(e)}', 'danger')

    return redirect(url_for('blockchain.view_blockchain'))


@blockchain_bp.route('/blockchain/verify')
@login_required
def verify_chain():
    """Verifikasi integritas blockchain"""
    blockchain = get_blockchain()

    if len(blockchain.chain) <= 1:
        flash('Blockchain belum memiliki cukup blok untuk diverifikasi.', 'info')
        return redirect(url_for('blockchain.view_blockchain'))

    if blockchain.is_chain_valid():
        flash('✅ Blockchain VALID! Semua blok terverifikasi dan tidak ada manipulasi.', 'success')
    else:
        flash('❌ Blockchain TIDAK VALID! Terdeteksi manipulasi data.', 'danger')

    return redirect(url_for('blockchain.view_blockchain'))


@blockchain_bp.route('/blockchain/assets')
@login_required
def list_assets():
    """Daftar semua aset yang diamankan blockchain"""
    assets = EncryptedAsset.query.filter_by(user_id=current_user.id).order_by(EncryptedAsset.timestamp.desc()).all()

    decrypted_assets = []
    for asset in assets:
        try:
            decrypted_data = db_decrypt(asset.asset_data_encrypted)
            decrypted_assets.append({
                'id': asset.id,
                'name': asset.asset_name,
                'data': decrypted_data,
                'block_index': asset.block_index,
                'timestamp': asset.timestamp
            })
        except Exception as e:
            decrypted_assets.append({
                'id': asset.id,
                'name': asset.asset_name,
                'data': f'[Gagal mendekripsi: {str(e)}]',
                'block_index': asset.block_index,
                'timestamp': asset.timestamp
            })

    return render_template('assets.html', assets=decrypted_assets)
