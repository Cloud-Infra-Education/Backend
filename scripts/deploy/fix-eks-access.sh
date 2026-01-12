#!/bin/bash
# EKS 클러스터 접근 권한 문제 해결 스크립트

set -e

CLUSTER_NAME="y2om-formation-lap-seoul"
REGION="ap-northeast-2"

echo "🔍 EKS 클러스터 접근 권한 확인 중..."
echo ""

# 현재 사용자 ARN 확인
CURRENT_USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
echo "현재 사용자 ARN: $CURRENT_USER_ARN"
echo ""

# Access Entries 확인
echo "📋 현재 EKS Access Entries:"
aws eks list-access-entries --cluster-name "$CLUSTER_NAME" --region "$REGION" 2>&1 || echo "⚠️  Access Entries를 확인할 수 없습니다."
echo ""

echo "========================================="
echo "해결 방법:"
echo "========================================="
echo ""
echo "현재 사용자가 EKS 클러스터에 접근 권한이 없는 것 같습니다."
echo ""
echo "옵션 1: Terraform으로 Access Entry 추가"
echo "  - Terraform 변수에 현재 사용자 ARN 추가"
echo "  - terraform apply 실행"
echo ""
echo "옵션 2: AWS CLI로 직접 추가 (임시)"
echo "  aws eks create-access-entry \\"
echo "    --cluster-name $CLUSTER_NAME \\"
echo "    --principal-arn $CURRENT_USER_ARN \\"
echo "    --type STANDARD \\"
echo "    --region $REGION"
echo ""
echo "  aws eks associate-access-policy \\"
echo "    --cluster-name $CLUSTER_NAME \\"
echo "    --principal-arn $CURRENT_USER_ARN \\"
echo "    --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \\"
echo "    --access-scope type=cluster \\"
echo "    --region $REGION"
echo ""
echo "옵션 3: 클러스터 관리자에게 접근 권한 요청"
echo "========================================="
