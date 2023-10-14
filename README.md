# Meet-Up-Spot
# 만남 장소 추천 서비스: 백엔드 API

이 프로젝트는 여러 주소를 기반으로 중간 위치 주변의 만남 장소를 추천해주는 백엔드 API입니다.

## 주요 기능

* 여러 주소 입력 및 중간 위치 계산:
  * 사용자는 여러 주소를 입력하게 되며, 이를 기반으로 중간 위치를 계산합니다.
* 중간 위치 주변 장소 추천:
  * 계산된 중간 위치를 기반으로 주변의 장소들을 추천합니다.
* 유저 기반 장소 추천:
  * 사용자의 과거 검색 이력, 선호 장소, 평점 등을 기반으로 개인화된 장소를 추천합니다.
 
## API Endpoints 
**구체적인 내용은 swagger를 통해 확인가능** 

### 관리자 관련 /admin
<details>
  
* 사용자 목록 조회
  * Endpoint: /users
  * Method: GET
* 사용자 생성
  * Endpoint: /create-user
  * Method: POST
* 특정 사용자 업데이트
  * Endpoint: /{user_id}
  * Method: PUT
  
</details>

### 사용자 관련 /users
<details>
  
  * 자신의 정보 업데이트
  * Endpoint: /me
  * Method: PUT
* 자신의 정보 조회
  * Endpoint: /me
  * Method: GET
* 사용자 등록
  * Endpoint: /register
  * Method: POST
* ID로 사용자 조회
  * Endpoint: /{user_id}
  * Method: GET
       
</details>

### 장소 추천 /places
<details>

* 추천 장소 요청
  * Endpoint: /request-places/
  * Method: POST
* 특정 장소 조회
  * Endpoint: /{place_id}
  * Method: GET
* 전체 장소 조회
  * Endpoint: /
  * Method: GET
* 장소 관심 표시
  * Endpoint: /{place_id}/mark
  * Method: POST
* 장소 관심 해제
  * Endpoint: /{place_id}/unmark
  * Method: DELETE
* 자동 완성 장소 조회
  * Endpoint: /completed-places/{address}
  * Method: GET
* 거리 매트릭스 조회
  * Endpoint: /{destination_id}/get-travel-info
  * Method: POST
  * Description: 주어진 출발지와 목적지를 기반으로 여행 정보를 조회합니다.
  
</details>

## ERD

 
``` mermaid
erDiagram
User ||--o{ Place : interested_places
    Place ||--o{ PlaceType : place_types
    Location ||--o{Place:places
    User ||--o{ GoogleMapsApiLog : google_maps_api_logs
    User ||--o{ UserSearchHistory : search_history_relations
    User ||--o{user_current_location_association: location_history
    Location ||--o{user_current_location_association: location_history
```

