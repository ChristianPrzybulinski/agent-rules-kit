# Tags verificadas no Docker Hub em 2026-09-29 (maven e eclipse-temurin, library/).
FROM maven:3.9-eclipse-temurin-25 AS build
WORKDIR /app
COPY pom.xml .
COPY . .
RUN ./mvnw -B -ntp -DskipTests package || mvn -B -ntp -DskipTests package

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=build /app/*/target/*.jar app.jar
# Em multi-módulo, o jar executável é o do módulo bootstrap; ajuste o glob se houver mais de um.
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
