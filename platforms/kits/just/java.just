# Java 25 + Maven recipes (agent-rules-kit, KIT-074), run from the Maven project folder (the one with mvnw).
# Always the Maven wrapper; MVN_FLAGS adds Maven options (CI sets -B -ntp).

mvn := './mvnw'
mvn_flags := env('MVN_FLAGS', '')

# run the Spring Boot application
run *ARGS:
    {{mvn}} {{mvn_flags}} spring-boot:run {{ARGS}}

# unit tests; Maven options pass through (just test -Dtest=SomeTest)
test *ARGS:
    {{mvn}} {{mvn_flags}} test {{ARGS}}

# the gate before a commit or PR: format check, then unit, integration and the pom's quality gates
verify:
    {{mvn}} {{mvn_flags}} spotless:check verify

# apply the formatter
fmt:
    {{mvn}} {{mvn_flags}} spotless:apply

# check the format without changing a file
lint:
    {{mvn}} {{mvn_flags}} spotless:check

# OWASP dependency-check, failing on CVSS 7 or more; needs NVD_API_KEY in the environment
dependency-check:
    {{mvn}} {{mvn_flags}} org.owasp:dependency-check-maven:13.0.0:check -DfailBuildOnCVSS=7 -DnvdApiKeyEnvironmentVariable=NVD_API_KEY
