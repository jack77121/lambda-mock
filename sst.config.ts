/// <reference path="./.sst/platform/config.d.ts" />

import { ApiGatewayV1RouteArgs, BucketArgs } from "./.sst/platform/src/components/aws";

const API_PLAN = {
  poxa: {
    name: "poxa-plan",
    throttle: {
      rate: 5000,
      burst: 2000,
    },
  },
};

// domian
const PROD_DOMAIN = "api.calc.poxa.app";
const STAGING_DOMAIN = "staging.api.calc.poxa.app";
// cert arn
const PROD_CERT_ARN =
  "arn:aws:acm:ap-northeast-1:485526649122:certificate/972045b7-7d52-46a4-a7b0-b06fc1f39deb";
const STAGING_CERT_ARN =
  "arn:aws:acm:ap-northeast-1:904610147815:certificate/b1c6e338-6092-446c-a4ad-4aa19e469f08";
// bucket name
const AWS_BUCKET_NAME = "poxa-calc";
// bucket cors setting
const PROD_BUCKET_CORS: BucketArgs["cors"] = {
  allowHeaders: ["*"],
  allowMethods: ["GET", "PUT"],
  allowOrigins: ["https://calc.poxa.io"],
  exposeHeaders: ["ETag"],
  maxAge: "3000 seconds",
};
const STAGING_BUCKET_CORS: BucketArgs["cors"] = {
  allowHeaders: ["*"],
  allowMethods: ["GET", "PUT"],
  allowOrigins: ["http://localhost:3000", "https://poxa-mock-calc.matoapps.com"],
  exposeHeaders: ["ETag"],
  maxAge: "3000 seconds",
};
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

function varByStage(stage: string) {
  switch (stage) {
    case "production":
      return {
        domainName: PROD_DOMAIN,
        certArn: PROD_CERT_ARN,
        s3Cors: PROD_BUCKET_CORS,
      };
    case "staging":
      return {
        domainName: STAGING_DOMAIN,
        certArn: STAGING_CERT_ARN,
        s3Cors: STAGING_BUCKET_CORS,
      };
    default:
      console.error("Invalid stage");
      return {};
  }
}

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
    if (stage !== "production" && stage !== "staging") {
      throw new Error("Invalid stage, you must declare the stage as 'production' or 'staging'");
    }

    const { domainName, certArn, s3Cors } = varByStage(stage);

    // S3
    const bucket = new sst.aws.Bucket(AWS_BUCKET_NAME, {
      cors: s3Cors,
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

    // energy storage system run_simulation
    apiGateway.route(
      APIs.runSimulation.v1.route,
      {
        ...APIs.runSimulation.v1.handler,
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
