# Tags verified on Docker Hub on 2026-09-29 (maven and eclipse-temurin, library/).
FROM maven:3.9-eclipse-temurin-25 AS build
WORKDIR /app
COPY pom.xml .
COPY . .
RUN ./mvnw -B -ntp -DskipTests package || mvn -B -ntp -DskipTests package

FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=build /app/*/target/*.jar app.jar
# In multi-module projects the executable jar is the bootstrap module's; adjust the glob if there is more than one.
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
