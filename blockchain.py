import hashlib
import json
import time
from models import db, BlockModel

class Blockchain:
    def __init__(self):
        pass

    def get_chain(self):
        return BlockModel.query.order_by(BlockModel.block_index).all()

    def generate_route_hash(self, route_warehouses_list):
        route_str = "->".join([str(wh_id) for wh_id in route_warehouses_list])
        return hashlib.sha256(route_str.encode('utf-8')).hexdigest()

    def create_genesis_block(self):
        if not BlockModel.query.filter_by(block_index=0).first():
            genesis_block = BlockModel(
                block_index=0,
                shipment_id="GENESIS",
                block_type="GENESIS_BLOCK",
                data=json.dumps({"message": "Genesis Block"}, sort_keys=True),
                previous_hash="0",
                current_hash="",
                timestamp=time.time()
            )
            genesis_block.current_hash = self.calculate_hash(
                genesis_block.block_index,
                genesis_block.previous_hash,
                genesis_block.timestamp,
                genesis_block.data,
                genesis_block.block_type
            )
            db.session.add(genesis_block)
            db.session.commit()
            
            try:
                from firebase_sync import sync_block_to_firebase
                sync_block_to_firebase(genesis_block)
            except Exception as e:
                print(f"Error syncing genesis block: {e}")

    def get_latest_block(self):
        return BlockModel.query.order_by(BlockModel.block_index.desc()).first()

    def add_block(self, shipment_id, block_type, data, warehouse_id=None, route_hash=None, verification_status=None, digital_proof_hash=None):
        latest_block = self.get_latest_block()
        new_index = latest_block.block_index + 1
        timestamp = time.time()
        data_str = json.dumps(data, sort_keys=True)
        previous_hash = latest_block.current_hash
        
        current_hash = self.calculate_hash(new_index, previous_hash, timestamp, data_str, block_type, warehouse_id, route_hash)

        new_block = BlockModel(
            block_index=new_index,
            shipment_id=shipment_id,
            block_type=block_type,
            warehouse_id=warehouse_id,
            data=data_str,
            previous_hash=previous_hash,
            current_hash=current_hash,
            route_hash=route_hash,
            verification_status=verification_status,
            digital_proof_hash=digital_proof_hash,
            timestamp=timestamp
        )
        db.session.add(new_block)
        db.session.commit()
        
        try:
            from firebase_sync import sync_block_to_firebase
            sync_block_to_firebase(new_block)
        except Exception as e:
            print(f"Error syncing block: {e}")
            
        return new_block

    def calculate_hash(self, index, previous_hash, timestamp, data, block_type, warehouse_id=None, route_hash=None):
        value = f"{index}{previous_hash}{timestamp}{data}{block_type}{warehouse_id or ''}{route_hash or ''}"
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def validate_chain(self):
        chain = self.get_chain()
        if not chain:
            return True, -1
            
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i-1]

            calculated_hash = self.calculate_hash(
                current_block.block_index,
                current_block.previous_hash,
                current_block.timestamp,
                current_block.data,
                current_block.block_type,
                current_block.warehouse_id,
                current_block.route_hash
            )
            
            if current_block.current_hash != calculated_hash:
                return False, current_block.block_index

            if current_block.previous_hash != previous_block.current_hash:
                return False, current_block.block_index

        return True, -1

    def simulate_tampering(self):
        block_to_tamper = BlockModel.query.filter(BlockModel.block_index > 0).order_by(BlockModel.block_index.asc()).first()
        
        if not block_to_tamper:
            block_to_tamper = BlockModel.query.filter_by(block_index=0).first()

        if block_to_tamper:
            try:
                tampered_data = json.loads(block_to_tamper.data)
                tampered_data['status'] = 'TAMPERED_STATUS'
                tampered_data['tampered'] = True
            except:
                tampered_data = {"tampered": True}
            
            block_to_tamper.data = json.dumps(tampered_data, sort_keys=True)
            db.session.commit()
            return True
        return False
