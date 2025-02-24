from flask import Blueprint, jsonify, request
from app import db
from app.models import NetworkObject, NetworkGroup, ServiceObject, ServiceGroup, Firewall
from sqlalchemy import or_

bp = Blueprint('object', __name__)

@bp.route('/list', methods=['GET'])
def list_objects():
    try:
        # 페이지네이션 파라미터
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 정렬 파라미터
        sort_by = request.args.get('sort_by', 'name')
        sort_desc = request.args.get('sort_desc', 'false').lower() == 'true'
        
        # 필터 파라미터
        search = request.args.get('search', '')
        object_type = request.args.get('type', '')
        firewall_id = request.args.get('firewall_id', type=int)

        # 기본 쿼리 생성
        queries = []
        if object_type in ['network', ''] or object_type == 'network':
            network_query = NetworkObject.query
            if search:
                network_query = network_query.filter(
                    or_(
                        NetworkObject.name.ilike(f'%{search}%'),
                        NetworkObject.value.ilike(f'%{search}%')
                    )
                )
            if firewall_id:
                network_query = network_query.filter(NetworkObject.firewall_id == firewall_id)
            queries.append(network_query)

        if object_type in ['network_group', ''] or object_type == 'network_group':
            network_group_query = NetworkGroup.query
            if search:
                network_group_query = network_group_query.filter(
                    or_(
                        NetworkGroup.name.ilike(f'%{search}%'),
                        NetworkGroup.members.ilike(f'%{search}%')
                    )
                )
            if firewall_id:
                network_group_query = network_group_query.filter(NetworkGroup.firewall_id == firewall_id)
            queries.append(network_group_query)

        if object_type in ['service', ''] or object_type == 'service':
            service_query = ServiceObject.query
            if search:
                service_query = service_query.filter(
                    or_(
                        ServiceObject.name.ilike(f'%{search}%'),
                        ServiceObject.port.ilike(f'%{search}%')
                    )
                )
            if firewall_id:
                service_query = service_query.filter(ServiceObject.firewall_id == firewall_id)
            queries.append(service_query)

        if object_type in ['service_group', ''] or object_type == 'service_group':
            service_group_query = ServiceGroup.query
            if search:
                service_group_query = service_group_query.filter(
                    or_(
                        ServiceGroup.name.ilike(f'%{search}%'),
                        ServiceGroup.members.ilike(f'%{search}%')
                    )
                )
            if firewall_id:
                service_group_query = service_group_query.filter(ServiceGroup.firewall_id == firewall_id)
            queries.append(service_group_query)

        # 결과 조합
        objects = []
        for query in queries:
            results = query.all()
            for obj in results:
                firewall = Firewall.query.get(obj.firewall_id)
                object_data = {
                    'id': obj.id,
                    'name': obj.name,
                    'type': obj.__class__.__name__.lower().replace('object', '').replace('group', '_group'),
                    'firewall_id': obj.firewall_id,
                    'firewall_name': firewall.name if firewall else 'Unknown'
                }

                if isinstance(obj, NetworkObject):
                    object_data.update({
                        'network_type': obj.type,
                        'value': obj.value
                    })
                elif isinstance(obj, ServiceObject):
                    object_data.update({
                        'protocol': obj.protocol,
                        'port': obj.port
                    })
                elif isinstance(obj, (NetworkGroup, ServiceGroup)):
                    object_data.update({
                        'members': obj.members.split(',') if obj.members else []
                    })

                objects.append(object_data)

        # 정렬
        objects.sort(
            key=lambda x: x.get(sort_by, ''),
            reverse=sort_desc
        )

        # 페이지네이션
        total = len(objects)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_objects = objects[start:end]

        return jsonify({
            'success': True,
            'data': {
                'objects': paginated_objects,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page,
                'per_page': per_page
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/add', methods=['POST'])
def add_object():
    try:
        data = request.form
        object_type = data.get('type')
        firewall_id = data.get('firewall_id', type=int)
        name = data.get('name')

        if not all([object_type, firewall_id, name]):
            return jsonify({
                'success': False,
                'error': '필수 필드가 누락되었습니다.'
            }), 400

        if object_type == 'network':
            obj = NetworkObject(
                firewall_id=firewall_id,
                name=name,
                type=data.get('network_type'),
                value=data.get('value')
            )
        elif object_type == 'service':
            obj = ServiceObject(
                firewall_id=firewall_id,
                name=name,
                protocol=data.get('protocol'),
                port=data.get('port')
            )
        elif object_type == 'network_group':
            obj = NetworkGroup(
                firewall_id=firewall_id,
                name=name,
                members=','.join(request.form.getlist('members'))
            )
        elif object_type == 'service_group':
            obj = ServiceGroup(
                firewall_id=firewall_id,
                name=name,
                members=','.join(request.form.getlist('members'))
            )
        else:
            return jsonify({
                'success': False,
                'error': '잘못된 객체 유형입니다.'
            }), 400

        db.session.add(obj)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '객체가 성공적으로 추가되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<int:id>', methods=['GET'])
def get_object(id):
    try:
        # 모든 객체 테이블에서 검색
        obj = (NetworkObject.query.get(id) or
               NetworkGroup.query.get(id) or
               ServiceObject.query.get(id) or
               ServiceGroup.query.get(id))

        if not obj:
            return jsonify({
                'success': False,
                'error': '객체를 찾을 수 없습니다.'
            }), 404

        data = {
            'id': obj.id,
            'name': obj.name,
            'type': obj.__class__.__name__.lower().replace('object', '').replace('group', '_group'),
            'firewall_id': obj.firewall_id
        }

        if isinstance(obj, NetworkObject):
            data.update({
                'network_type': obj.type,
                'value': obj.value
            })
        elif isinstance(obj, ServiceObject):
            data.update({
                'protocol': obj.protocol,
                'port': obj.port
            })
        elif isinstance(obj, (NetworkGroup, ServiceGroup)):
            data.update({
                'member_ids': obj.members.split(',') if obj.members else []
            })

        return jsonify({
            'success': True,
            'object': data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<int:id>', methods=['DELETE'])
def delete_object(id):
    try:
        # 모든 객체 테이블에서 검색
        obj = (NetworkObject.query.get(id) or
               NetworkGroup.query.get(id) or
               ServiceObject.query.get(id) or
               ServiceGroup.query.get(id))

        if not obj:
            return jsonify({
                'success': False,
                'error': '객체를 찾을 수 없습니다.'
            }), 404

        name = obj.name
        db.session.delete(obj)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '객체가 성공적으로 삭제되었습니다.'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/available-members', methods=['GET'])
def get_available_members():
    try:
        object_type = request.args.get('type')
        firewall_id = request.args.get('firewall_id', type=int)

        if not all([object_type, firewall_id]):
            return jsonify({
                'success': False,
                'error': '필수 파라미터가 누락되었습니다.'
            }), 400

        if object_type == 'network_group':
            objects = NetworkObject.query.filter_by(firewall_id=firewall_id).all()
        elif object_type == 'service_group':
            objects = ServiceObject.query.filter_by(firewall_id=firewall_id).all()
        else:
            return jsonify({
                'success': False,
                'error': '잘못된 객체 유형입니다.'
            }), 400

        return jsonify({
            'success': True,
            'objects': [{
                'id': obj.id,
                'name': obj.name
            } for obj in objects]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 