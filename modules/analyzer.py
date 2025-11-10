# modules/analyzer.py
"""
블루오션 분석 및 결과 출력 모듈

FR-005: 블루오션 분석
- FR-005-1: 필터링 로직
- FR-005-2: 기회 점수 계산
- FR-005-3: 상태 라벨링

FR-006: 결과 출력
- FR-006-1: 터미널 출력
- FR-006-2: 엑셀 출력
"""

import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
from loguru import logger
import config
from modules.utils import create_output_filename, format_number


@dataclass
class KeywordAnalysis:
    """키워드 분석 결과"""
    keyword: str
    monthly_volume: int
    product_count: int
    is_blue_ocean: bool
    opportunity_score: float
    status: str


class BlueOceanAnalyzer:
    """블루오션 분석기"""

    def __init__(self):
        pass

    def calculate_opportunity_score(
        self,
        search_volume: int,
        product_count: int
    ) -> float:
        """
        FR-005-2: 기회 점수 계산

        공식: (검색량 점수 50점) + (경쟁 점수 50점)
        - 검색량 점수 = (volume / 20,000) * 50
        - 경쟁 점수 = ((15 - product_count) / 15) * 50

        Args:
            search_volume: 월 검색량
            product_count: 상품 개수

        Returns:
            기회 점수 (0-100)
        """
        # 검색량 점수 (0-50)
        volume_score = min((search_volume / config.MAX_SEARCH_VOLUME) * 50, 50)

        # 경쟁 점수 (0-50)
        if product_count <= config.MAX_PRODUCT_COUNT:
            competition_score = ((config.MAX_PRODUCT_COUNT - product_count) / config.MAX_PRODUCT_COUNT) * 50
        else:
            # 상품이 너무 많으면 감점
            competition_score = max(0, 25 - (product_count - config.MAX_PRODUCT_COUNT) * 2)

        total_score = volume_score + competition_score

        return round(total_score, 1)

    def get_status_label(
        self,
        search_volume: int,
        product_count: int,
        is_blue_ocean: bool
    ) -> str:
        """
        FR-005-3: 상태 라벨링

        Args:
            search_volume: 월 검색량
            product_count: 상품 개수
            is_blue_ocean: 블루오션 여부

        Returns:
            상태 라벨
        """
        if is_blue_ocean:
            return "✅ 블루오션"

        # 블루오션이 아닌 경우 이유 판단
        if search_volume < config.MIN_SEARCH_VOLUME:
            return "⚠️ 수요부족"
        elif search_volume > config.MAX_SEARCH_VOLUME:
            return "⚠️ 레드오션"
        elif product_count > config.MAX_PRODUCT_COUNT:
            return "❌ 경쟁과다"
        elif product_count < config.MIN_PRODUCT_COUNT:
            return "△ 틈새시장"
        else:
            return "△ 검토필요"

    def is_blue_ocean(
        self,
        search_volume: int,
        product_count: int
    ) -> bool:
        """
        FR-005-1: 블루오션 필터링 로직

        조건:
        - 검색량: 5,000 <= volume <= 20,000
        - 상품 수: 5 <= count <= 15

        Args:
            search_volume: 월 검색량
            product_count: 상품 개수

        Returns:
            블루오션 여부
        """
        volume_ok = config.MIN_SEARCH_VOLUME <= search_volume <= config.MAX_SEARCH_VOLUME
        count_ok = config.MIN_PRODUCT_COUNT <= product_count <= config.MAX_PRODUCT_COUNT

        return volume_ok and count_ok

    def analyze(
        self,
        keywords: List[str],
        search_volumes: Dict[str, int],
        product_counts: Dict[str, int]
    ) -> List[KeywordAnalysis]:
        """
        전체 키워드 분석

        Args:
            keywords: 키워드 리스트
            search_volumes: {키워드: 검색량}
            product_counts: {키워드: 상품개수}

        Returns:
            분석 결과 리스트
        """
        logger.info(f"블루오션 분석 시작: {len(keywords)}개 키워드")

        results = []

        for keyword in keywords:
            volume = search_volumes.get(keyword, 0)
            count = product_counts.get(keyword, 0)

            # 블루오션 판정
            blue_ocean = self.is_blue_ocean(volume, count)

            # 기회 점수 계산
            score = self.calculate_opportunity_score(volume, count)

            # 상태 라벨
            status = self.get_status_label(volume, count, blue_ocean)

            # 결과 저장
            analysis = KeywordAnalysis(
                keyword=keyword,
                monthly_volume=volume,
                product_count=count,
                is_blue_ocean=blue_ocean,
                opportunity_score=score,
                status=status
            )

            results.append(analysis)

        # 기회 점수 내림차순 정렬
        results.sort(key=lambda x: x.opportunity_score, reverse=True)

        # 통계
        blue_ocean_count = sum(1 for r in results if r.is_blue_ocean)
        logger.info(f"블루오션 분석 완료: {blue_ocean_count}/{len(results)}개 발견")

        return results

    def print_results(
        self,
        results: List[KeywordAnalysis],
        category: str,
        top_n: int = None
    ):
        """
        FR-006-1: 터미널 출력

        Args:
            results: 분석 결과
            category: 카테고리명
            top_n: 상위 N개 출력 (기본값: config.TOP_N_RESULTS)
        """
        if top_n is None:
            top_n = config.TOP_N_RESULTS

        # 블루오션만 필터링
        blue_oceans = [r for r in results if r.is_blue_ocean]

        print("\n" + "="*70)
        print("📊 분석 결과")
        print("="*70)

        if blue_oceans:
            print(f"\n🎉 블루오션 {len(blue_oceans)}개 발견!")
            print(f"\n추천 키워드 TOP {min(top_n, len(blue_oceans))}:")
            print("-"*70)

            for i, result in enumerate(blue_oceans[:top_n], 1):
                print(f"\n{i}. {result.keyword}")
                print(f"   💰 검색량: {format_number(result.monthly_volume)}/월 | "
                      f"📦 상품: {result.product_count}개")
                print(f"   ⭐ 기회점수: {result.opportunity_score}/100")

        else:
            print("\n😢 블루오션을 찾지 못했습니다.")
            print("\n대안:")
            print("  1. 다른 카테고리 시도")
            print("  2. config.py에서 블루오션 기준 조정")
            print("\n참고용 상위 키워드:")
            print("-"*70)

            for i, result in enumerate(results[:top_n], 1):
                print(f"\n{i}. {result.keyword} - {result.status}")
                print(f"   💰 검색량: {format_number(result.monthly_volume)}/월 | "
                      f"📦 상품: {result.product_count}개")
                print(f"   ⭐ 기회점수: {result.opportunity_score}/100")

        print("\n" + "="*70)

    def export_to_excel(
        self,
        results: List[KeywordAnalysis],
        category: str,
        output_path: str = None
    ) -> str:
        """
        FR-006-2: 엑셀 출력

        Args:
            results: 분석 결과
            category: 카테고리명
            output_path: 출력 파일 경로 (기본값: 자동 생성)

        Returns:
            저장된 파일 경로
        """
        if output_path is None:
            output_path = create_output_filename(category)

        logger.info(f"엑셀 파일 생성: {output_path}")

        # 데이터프레임 변환
        df_all = pd.DataFrame([
            {
                '키워드': r.keyword,
                '월 검색량': r.monthly_volume,
                '쿠팡 상품수': r.product_count,
                '블루오션 여부': '예' if r.is_blue_ocean else '아니오',
                '기회점수': r.opportunity_score,
                '상태': r.status
            }
            for r in results
        ])

        # 블루오션만 필터링
        df_blue_ocean = df_all[df_all['블루오션 여부'] == '예'].copy()

        # 통계 데이터
        stats_data = {
            '항목': [
                '총 키워드 수',
                '블루오션 수',
                '블루오션 비율',
                '평균 검색량',
                '평균 상품 수',
                '최고 기회점수',
                '분석 카테고리'
            ],
            '값': [
                len(results),
                len(df_blue_ocean),
                f"{len(df_blue_ocean)/len(results)*100:.1f}%" if results else "0%",
                f"{df_all['월 검색량'].mean():.0f}" if not df_all.empty else "0",
                f"{df_all['쿠팡 상품수'].mean():.0f}" if not df_all.empty else "0",
                f"{df_all['기회점수'].max():.1f}" if not df_all.empty else "0",
                category
            ]
        }
        df_stats = pd.DataFrame(stats_data)

        # 엑셀 작성
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 시트 1: 전체 분석
            df_all.to_excel(writer, sheet_name='전체분석', index=False)

            # 시트 2: 블루오션만
            if not df_blue_ocean.empty:
                df_blue_ocean.to_excel(writer, sheet_name='블루오션', index=False)

            # 시트 3: 통계
            df_stats.to_excel(writer, sheet_name='통계', index=False)

            # 서식 적용
            self._apply_excel_formatting(writer, df_all, df_blue_ocean, df_stats)

        logger.info(f"엑셀 파일 저장 완료: {output_path}")

        return output_path

    def _apply_excel_formatting(
        self,
        writer,
        df_all: pd.DataFrame,
        df_blue_ocean: pd.DataFrame,
        df_stats: pd.DataFrame
    ):
        """엑셀 서식 적용"""
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter

        workbook = writer.book

        # 시트별 서식 적용
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]

            # 헤더 서식
            for cell in worksheet[1]:
                cell.font = Font(bold=True, size=11)
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(bold=True, size=11, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center')

            # 열 너비 자동 조정
            for column in worksheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # 모든 셀 가운데 정렬
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(horizontal='center', vertical='center')


def main():
    """테스트용 메인 함수"""
    from modules.utils import setup_logger

    setup_logger()

    print("="*50)
    print("📊 블루오션 분석 테스트")
    print("="*50)

    # 테스트 데이터
    keywords = ["주방용품", "밀폐용기", "김치냉장고용기", "냉동실정리"]
    search_volumes = {"주방용품": 15000, "밀폐용기": 8000, "김치냉장고용기": 6700, "냉동실정리": 12400}
    product_counts = {"주방용품": 50, "밀폐용기": 12, "김치냉장고용기": 6, "냉동실정리": 8}

    # 분석
    analyzer = BlueOceanAnalyzer()
    results = analyzer.analyze(keywords, search_volumes, product_counts)

    # 출력
    analyzer.print_results(results, "주방")

    # 엑셀 저장
    excel_path = analyzer.export_to_excel(results, "주방_테스트")
    print(f"\n📁 엑셀 파일 저장: {excel_path}")


if __name__ == '__main__':
    main()
