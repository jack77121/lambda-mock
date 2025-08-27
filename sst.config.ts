/// <reference path="./.sst/platform/config.d.ts" />

import { ApiGatewayV1RouteArgs, BucketArgs } from "./.sst/platform/src/components/aws";

const API_PLAN = {
  poxa: {
    name: "poxa-plan",
    throttle: {
      rate: 100,
      burst: 100,
    },
  },
};

// domian
const PROD_DOMAIN = "api.calc.poxa.app";
const STAGING_DOMAIN = "staging.api.calc.poxa.app";
// bucket name
const AWS_BUCKET_NAME = "poxa-calc";
// bucket cors setting
const PROD_BUCKET_CORS = [];
const STAGING_BUCKET_CORS: BucketArgs["cors"] = {
  allowHeaders: ["*"],
  allowMethods: ["GET", "PUT"],
  allowOrigins: ["http://localhost:3000", "https://poxa-mock-calc.matoapps.com"],
  exposeHeaders: ["ETag"],
  maxAge: "3000 seconds",
};
const ESS_IRR_EVALUATION = "ess-irr-evaluation";
const RUN_SIMULATION = "run-simulation";

const APIs: Record<
  string,
  Record<
    string,
    {
      route: string;
      handler: sst.aws.FunctionArgs;
      args?: ApiGatewayV1RouteArgs;
    }
  >
> = {
  essIrrEvaluation: {
    v1: {
      route: "POST /v1/ess-irr-evaluation",
      handler: {
        name: ESS_IRR_EVALUATION,
        python: {
          container: true,
        },
        runtime: "python3.11",
        handler: "./v1_lambda_ess_irr_evaluation/src/v1_lambda_ess_irr_evaluation/api.handler",
        timeout: "2 minutes",
        memory: "512 MB",
      },
      args: {
        apiKey: true,
      },
    },
  },
  runSimulation: {
    v1: {
      route: "POST /v1/run-simulation",
      handler: {
        name: RUN_SIMULATION,
        python: {
          container: true,
        },
        runtime: "python3.11",
        handler: "./v1_lambda_run_simulation/src/v1_lambda_run_simulation/api.handler",
        timeout: "2 minutes",
        memory: "256 MB",
      },
      args: {
        apiKey: true,
      },
    },
  },
};

export default $config({
  app(input) {
    return {
      name: "poxa-calc-backend",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: ["production"].includes(input?.stage),
      home: "aws",
      providers: {
        aws: {
          profile: input.stage === "production" ? "calc-poxa-production" : "calc-poxa-staging",
        },
      },
    };
  },
  async run() {
    const stage = $app.stage;
    const domainName = stage === "production" ? PROD_DOMAIN : STAGING_DOMAIN;
    const certArn =
      stage === "production"
        ? "arn:aws:acm:ap-northeast-1:485526649122:certificate/34bb6dbf-24cd-4fe8-9b42-424f2548ee3f"
        : "arn:aws:acm:ap-northeast-1:904610147815:certificate/b1c6e338-6092-446c-a4ad-4aa19e469f08";
    const POSTGRES_URL = new sst.Secret("POSTGRES_URL").value;

    // S3
    const bucket = new sst.aws.Bucket(AWS_BUCKET_NAME, {
      cors: STAGING_BUCKET_CORS,
    });

    // API Gateway
    const apiGateway = new sst.aws.ApiGatewayV1("CalcApiGateway", {
      accessLog: {
        retention: "2 months",
      },
      domain: {
        name: domainName,
        dns: false,
        cert: certArn,
      },
      endpoint: {
        type: "regional",
      },
    });

    // Add routes to the API Gateway

    // energy storage system irr evaluation (run_all_simulations)
    apiGateway.route(
      APIs.essIrrEvaluation.v1.route,
      {
        ...APIs.essIrrEvaluation.v1.handler,
        environment: { POSTGRES_URL },
      },
      { ...APIs.essIrrEvaluation.v1.args }
    );
    // energy storage system run_simulation
    apiGateway.route(
      APIs.runSimulation.v1.route,
      {
        ...APIs.runSimulation.v1.handler,
        environment: { POSTGRES_URL },
      },
      { ...APIs.runSimulation.v1.args }
    );

    // must deploy before adding usage plan
    apiGateway.deploy();

    // add usage plan
    apiGateway.addUsagePlan(API_PLAN.poxa.name, {
      throttle: API_PLAN.poxa.throttle,
    });

    //!: add api key to usage plan MANUALLY ON AWS api gateway

    return {
      apiGateway: apiGateway.url,
      bucket: bucket.name,
    };
  },
});
